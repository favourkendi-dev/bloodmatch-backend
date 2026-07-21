from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from donors.models import DonorProfile
from .models import BloodRequest
from .serializers import BloodRequestSerializer, MatchedDonorSerializer
from .compatibility import get_compatible_donor_types


class IsHospitalOwnerOrReadOnly(permissions.BasePermission):
    """
    Only the hospital that owns a request can edit/delete it.
    Everyone authenticated can read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.hospital.user == request.user


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
    Returns compatible, available, same-city donors for this request.
    Hospital-owner only.
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
        donors = DonorProfile.objects.filter(
            blood_type__in=compatible_types,
            city=blood_request.city,
            is_available=True,
        )
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
        try:
            donor = DonorProfile.objects.get(
                id=donor_id,
                blood_type__in=compatible_types,
                city=blood_request.city,
                is_available=True,
            )
        except DonorProfile.DoesNotExist:
            return Response(
                {"detail": "Donor not found or not eligible for this request."},
                status=400
            )

        blood_request.matched_donor = donor
        blood_request.status = 'in_progress'
        blood_request.save()

        serializer = BloodRequestSerializer(blood_request)
        return Response(serializer.data)
