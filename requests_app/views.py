from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from donors.models import DonorProfile, Donation, DonorHealthCheck
from .models import BloodRequest
from .serializers import BloodRequestSerializer, MatchedDonorSerializer
from .compatibility import get_compatible_donor_types
from notifications.models import Notification
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
            if distance <= donor.max_distance_km:
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


class BloodRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/requests/<id>/  -> anyone authenticated can view
    PATCH  /api/requests/<id>/  -> hospital owner only, and only while status='open'
    DELETE /api/requests/<id>/  -> hospital owner only, and only while status='open'

    We only allow edit/delete while the request is still 'open' so we never
    orphan a matched donor, a donation record, or an active chat thread.
    """
    serializer_class = BloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsHospitalOwnerOrReadOnly]
    queryset = BloodRequest.objects.all()

    def perform_update(self, serializer):
        if serializer.instance.status != 'open':
            raise PermissionDenied(
                "This request can no longer be edited because a donor is already matched to it."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != 'open':
            raise PermissionDenied(
                "This request can no longer be deleted because a donor is already matched to it. "
                "Cancel it instead."
            )
        instance.delete()


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

        # Lock: once a request is no longer open, nobody else can be matched to it.
        if blood_request.status != 'open':
            return Response(
                {"detail": "This request already has a matched donor and is no longer open for selection."},
                status=400
            )

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

        health_fields = [
            'feeling_well', 'no_recent_tattoo_or_piercing',
            'no_recent_travel_risk', 'not_on_medication',
            'meets_weight_minimum',
        ]
        health_answers = {f: request.data.get(f) for f in health_fields}
        if not all(health_answers.values()):
            return Response(
                {"detail": "You must confirm all health screening questions to accept."},
                status=400
            )

        blood_request.donor_confirmed = True
        blood_request.save()

        donation = blood_request.donation_record.filter(status=Donation.Status.PENDING).first()
        if donation:
            donation.status = Donation.Status.ACCEPTED
            donation.save()
            DonorHealthCheck.objects.update_or_create(donation=donation, defaults=health_answers)

        if blood_request.hospital and blood_request.hospital.user:
            Notification.objects.create(
                user=blood_request.hospital.user,
                notification_type=Notification.NotificationType.REQUEST_MATCHED,
                message=f"{request.user.username} has accepted your blood request for {blood_request.blood_type}."
            )

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)


class DeclineDonorRequestView(APIView):
    """
    POST /api/requests/<id>/decline/
    Matched-donor only. Declines the request, freeing it up for another donor.

    Works whether the donor already confirmed (donor_confirmed=True) or not,
    so a donor can change their mind even after accepting -- as long as the
    hospital hasn't marked it fulfilled or cancelled yet.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'donor_profile') or blood_request.matched_donor != request.user.donor_profile:
            raise PermissionDenied("Only the matched donor can decline this request.")

        if blood_request.status != 'in_progress':
            return Response(
                {"detail": "This request is not currently matched to you."},
                status=400
            )

        was_confirmed = blood_request.donor_confirmed

        donation = blood_request.donation_record.filter(
            status__in=[Donation.Status.PENDING, Donation.Status.ACCEPTED]
        ).first()
        if donation:
            donation.status = Donation.Status.DECLINED
            donation.save()

        blood_request.matched_donor = None
        blood_request.status = 'open'
        blood_request.donor_confirmed = False
        blood_request.save()

        if blood_request.hospital and blood_request.hospital.user:
            note = (
                f"{request.user.username} changed their mind and is no longer able to donate "
                f"for your {blood_request.blood_type} request. It's open again."
                if was_confirmed else
                f"{request.user.username} declined your {blood_request.blood_type} blood request. "
                f"It's open again."
            )
            Notification.objects.create(
                user=blood_request.hospital.user,
                notification_type=Notification.NotificationType.REQUEST_CANCELLED,
                message=note,
            )

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


class HospitalAnalyticsView(APIView):
    """
    GET /api/requests/analytics/
    Hospital-only. Returns analytics data for the logged-in hospital.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'hospital_profile'):
            raise PermissionDenied("Only hospitals can view analytics.")

        hospital = request.user.hospital_profile
        requests = BloodRequest.objects.filter(hospital=hospital)

        total = requests.count()
        fulfilled = requests.filter(status='fulfilled').count()
        cancelled = requests.filter(status='cancelled').count()
        open_reqs = requests.filter(status='open').count()
        in_progress = requests.filter(status='in_progress').count()

        fulfillment_rate = round((fulfilled / total) * 100, 1) if total > 0 else 0

        fulfilled_requests = requests.filter(status='fulfilled', matched_donor__isnull=False)
        time_to_match_list = []
        for req in fulfilled_requests:
            if req.matched_donor:
                time_to_match_list.append((req.updated_at - req.created_at).total_seconds() / 3600)

        avg_time_to_match = round(sum(time_to_match_list) / len(time_to_match_list), 1) if time_to_match_list else 0

        blood_type_counts = {}
        for req in requests:
            blood_type_counts[req.blood_type] = blood_type_counts.get(req.blood_type, 0) + 1

        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        months = []
        for i in range(5, -1, -1):
            month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            count = requests.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            months.append({
                'month': month_start.strftime('%b'),
                'count': count
            })

        return Response({
            'total_requests': total,
            'fulfilled': fulfilled,
            'cancelled': cancelled,
            'open': open_reqs,
            'in_progress': in_progress,
            'fulfillment_rate': fulfillment_rate,
            'avg_time_to_match_hours': avg_time_to_match,
            'blood_type_demand': blood_type_counts,
            'requests_per_month': months,
        })


class VolunteerForRequestView(APIView):
    """
    POST /api/requests/<id>/volunteer/
    Donor-only. Allows a donor to volunteer for an open request directly.
    Sets matched_donor to this donor and status='in_progress'.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        if not hasattr(request.user, 'donor_profile'):
            raise PermissionDenied("Only donors can volunteer for requests.")

        if blood_request.status != 'open':
            return Response(
                {"detail": "This request is no longer open for volunteers."},
                status=400
            )

        donor = request.user.donor_profile

        compatible_types = get_compatible_donor_types(blood_request.blood_type)
        if donor.blood_type not in compatible_types:
            return Response(
                {"detail": "Your blood type is not compatible with this request."},
                status=400
            )

        if not donor.is_available:
            return Response(
                {"detail": "You must mark yourself as available to volunteer."},
                status=400
            )

        health_fields = [
            'feeling_well', 'no_recent_tattoo_or_piercing',
            'no_recent_travel_risk', 'not_on_medication',
            'meets_weight_minimum',
        ]
        health_answers = {f: request.data.get(f) for f in health_fields}
        if not all(health_answers.values()):
            return Response(
                {"detail": "You must confirm all health screening questions to volunteer."},
                status=400
            )

        blood_request.matched_donor = donor
        blood_request.status = 'in_progress'
        blood_request.save()

        donation = Donation.objects.create(
            donor=donor,
            blood_request=blood_request,
            units_donated=blood_request.units_needed,
            status=Donation.Status.PENDING,
        )
        DonorHealthCheck.objects.update_or_create(donation=donation, defaults=health_answers)

        if blood_request.hospital and blood_request.hospital.user:
            Notification.objects.create(
                user=blood_request.hospital.user,
                notification_type=Notification.NotificationType.REQUEST_MATCHED,
                message=f"{request.user.username} has volunteered for your {blood_request.blood_type} blood request."
            )

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)
