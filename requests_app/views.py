from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from donors.models import DonorProfile, Donation
from .models import BloodRequest
from .serializers import BloodRequestSerializer, MatchedDonorSerializer
from .compatibility import get_compatible_donor_types
from .geo import calculate_distance_km

# Maximum distance (in km) a donor can be from a request to be considered a match.
MATCH_RADIUS_KM = 50


class IsHospitalOwnerOrReadOnly(permissions.BasePermission):
    """
    Only the hospital that owns a request can edit/delete it.
    Everyone authenticated can read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.hospital.user == request.user


def get_eligible_donors(blood_request, compatible_types):
    """
    Returns a list of eligible DonorProfile objects for a request, with
    `_distance_km` attached to each (or None if distance couldn't be calculated).

    - If the request has coordinates: donors WITH coordinates are filtered to
      within MATCH_RADIUS_KM and get a real _distance_km. Donors WITHOUT
      coordinates fall back to a city text-match, with _distance_km=None.
    - If the request has no coordinates: everyone falls back to city text-match.
    """
    candidates = DonorProfile.objects.filter(
        blood_type__in=compatible_types,
        is_available=True,
    )

    request_has_coords = blood_request.latitude is not None and blood_request.longitude is not None

    eligible = []
    for donor in candidates:
        donor_has_coords = donor.latitude is not None and donor.longitude is not None

        if request_has_coords and donor_has_coords:
            distance = calculate_distance_km(
                blood_request.latitude, blood_request.longitude,
                donor.latitude, donor.longitude,
            )
            if distance <= MATCH_RADIUS_KM:
                donor._distance_km = distance
                eligible.append(donor)
        else:
            # Fall back to city match when either side lacks coordinates
            if donor.city == blood_request.city:
                donor._distance_km = None
                eligible.append(donor)

    # Closest first; donors with unknown distance (None) sort last
    eligible.sort(key=lambda d: (d._distance_km is None, d._distance_km))
    return eligible


class BloodRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'hospital_profile'):
            return BloodRequest.objects.filter(hospital=user.hospital_profile)
        return BloodRequest.objects.filter(status='open')

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'hospital_profile'):
            raise PermissionDenied("Only hospitals can create blood requests.")
        serializer.save(hospital=user.hospital_profile)


class BloodRequestDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalOwnerOrReadOnly]
    queryset = BloodRequest.objects.all()


class MatchingDonorsView(APIView):
    """
    GET /api/requests/<id>/matches/
    Returns compatible, available donors within MATCH_RADIUS_KM of this
    request (or same-city, for donors/requests without coordinates yet),
    sorted closest first. Hospital-owner only.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'hospital_profile') or blood_request.hospital.user != request.user:
            raise PermissionDenied("Only the owning hospital can view matches for this request.")

        compatible_types = get_compatible_donor_types(blood_request.blood_type)
        donors = get_eligible_donors(blood_request, compatible_types)
        serializer = MatchedDonorSerializer(donors, many=True)
        return Response(serializer.data)


class SelectDonorView(APIView):
    """
    POST /api/requests/<id>/select_donor/
    Body: {"donor_id": <DonorProfile id>}
    Hospital-owner only. Sets matched_donor and status='in_progress'.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'hospital_profile') or blood_request.hospital.user != request.user:
            raise PermissionDenied("Only the owning hospital can select a donor for this request.")

        donor_id = request.data.get('donor_id')
        if not donor_id:
            return Response({"detail": "donor_id is required."}, status=400)

        compatible_types = get_compatible_donor_types(blood_request.blood_type)
        eligible_donors = get_eligible_donors(blood_request, compatible_types)
        donor = next((d for d in eligible_donors if str(d.id) == str(donor_id)), None)

        if donor is None:
            return Response(
                {"detail": "Donor not found or not eligible for this request."},
                status=400
            )

        blood_request.matched_donor = donor
        blood_request.status = 'in_progress'
        blood_request.save()

        Donation.objects.create(
            donor=donor,
            blood_request=blood_request,
            units_donated=blood_request.units_needed,
            status=Donation.Status.PENDING,
        )

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class FulfillRequestView(APIView):
    """
    POST /api/requests/<id>/fulfill/
    Hospital-owner only. Marks an in_progress request as fulfilled.
    Creates a Donation record for the matched donor and updates
    their last_donation_date.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'hospital_profile') or blood_request.hospital.user != request.user:
            raise PermissionDenied("Only the owning hospital can fulfill this request.")

        if blood_request.status != 'in_progress':
            return Response(
                {"detail": f"Cannot fulfill a request with status '{blood_request.status}'. Must be 'in_progress'."},
                status=400
            )

        blood_request.status = 'fulfilled'
        blood_request.save()

        if blood_request.matched_donor:
            donation = blood_request.donation_record.exclude(
                status__in=[Donation.Status.CANCELLED, Donation.Status.DECLINED]
            ).first()
            if donation:
                donation.status = Donation.Status.COMPLETED
                donation.save()
                blood_request.matched_donor.last_donation_date = donation.donation_date
                blood_request.matched_donor.save()

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class CancelRequestView(APIView):
    """
    POST /api/requests/<id>/cancel/
    Hospital-owner only. Cancels a request that's open or in_progress.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'hospital_profile') or blood_request.hospital.user != request.user:
            raise PermissionDenied("Only the owning hospital can cancel this request.")

        if blood_request.status not in ('open', 'in_progress'):
            return Response(
                {"detail": f"Cannot cancel a request with status '{blood_request.status}'."},
                status=400
            )

        donation = blood_request.donation_record.filter(
            status__in=[Donation.Status.PENDING, Donation.Status.ACCEPTED]
        ).first()
        if donation:
            donation.status = Donation.Status.CANCELLED
            donation.save()

        blood_request.status = 'cancelled'
        blood_request.save()

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class AcceptDonorRequestView(APIView):
    """
    POST /api/requests/<id>/accept/
    Matched-donor only. Confirms the donor accepts this request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'donor_profile') or blood_request.matched_donor != request.user.donor_profile:
            raise PermissionDenied("Only the matched donor can accept this request.")

        if blood_request.status != 'in_progress' or blood_request.donor_confirmed:
            return Response(
                {"detail": "This request is not awaiting your confirmation."},
                status=400
            )

        blood_request.donor_confirmed = True
        blood_request.save()

        donation = blood_request.donation_record.filter(status=Donation.Status.PENDING).first()
        if donation:
            donation.status = Donation.Status.ACCEPTED
            donation.save()

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class DeclineDonorRequestView(APIView):
    """
    POST /api/requests/<id>/decline/
    Matched-donor only. Declines the request, freeing it up for another donor.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'donor_profile') or blood_request.matched_donor != request.user.donor_profile:
            raise PermissionDenied("Only the matched donor can decline this request.")

        if blood_request.status != 'in_progress' or blood_request.donor_confirmed:
            return Response(
                {"detail": "This request is not awaiting your confirmation."},
                status=400
            )

        donation = blood_request.donation_record.filter(status=Donation.Status.PENDING).first()
        if donation:
            donation.status = Donation.Status.DECLINED
            donation.save()

        blood_request.matched_donor = None
        blood_request.status = 'open'
        blood_request.donor_confirmed = False
        blood_request.save()

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class MyMatchedRequestsView(generics.ListAPIView):
    """
    GET /api/requests/my_matches/
    Donor-only. Returns all requests this donor has been matched to,
    regardless of status (in_progress, fulfilled, cancelled).
    """
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'donor_profile'):
            return BloodRequest.objects.none()
        return BloodRequest.objects.filter(matched_donor=user.donor_profile).order_by('-updated_at')
