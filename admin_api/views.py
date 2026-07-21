from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from hospitals.models import HospitalProfile
from donors.models import DonorProfile
from requests_app.models import BloodRequest
from .serializers import AdminHospitalSerializer, AdminDonorSerializer, AdminBloodRequestSerializer
from .permissions import IsAdminRole


class AdminHospitalListView(generics.ListAPIView):
    """
    GET /api/admin/hospitals/
    Admin-only. Lists all hospital accounts and their verification status.
    """
    serializer_class = AdminHospitalSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = HospitalProfile.objects.all().order_by('-created_at')


class VerifyHospitalView(APIView):
    """
    POST /api/admin/hospitals/<id>/verify/
    Admin-only. Marks a hospital as verified and records the audit trail
    (which admin verified it, and when).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        try:
            hospital = HospitalProfile.objects.get(pk=pk)
        except HospitalProfile.DoesNotExist:
            raise NotFound("Hospital not found.")
        hospital.is_verified = True
        hospital.verified_by = request.user
        hospital.verified_at = timezone.now()
        hospital.save()
        serializer = AdminHospitalSerializer(hospital)
        return Response(serializer.data)


class AdminDonorListView(generics.ListAPIView):
    """
    GET /api/admin/donors/
    Admin-only. Lists all donor accounts.
    """
    serializer_class = AdminDonorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = DonorProfile.objects.all().order_by('-created_at')


class AdminRequestListView(generics.ListAPIView):
    """
    GET /api/admin/requests/
    Admin-only. Lists every blood request in the system, any status, any hospital.
    """
    serializer_class = AdminBloodRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
    queryset = BloodRequest.objects.all().order_by('-created_at')


class AdminCancelRequestView(APIView):
    """
    POST /api/admin/requests/<id>/cancel/
    Admin-only. Force-cancels any request regardless of status or ownership.
    Used for moderation (e.g. spam, abuse, duplicate requests).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        try:
            blood_request = BloodRequest.objects.get(pk=pk)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")
        blood_request.status = 'cancelled'
        blood_request.save()
        serializer = AdminBloodRequestSerializer(blood_request)
        return Response(serializer.data)


class AdminReportsView(APIView):
    """
    GET /api/admin/reports/
    Admin-only. Basic platform stats.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request):
        data = {
            "total_donors": DonorProfile.objects.count(),
            "total_hospitals": HospitalProfile.objects.count(),
            "verified_hospitals": HospitalProfile.objects.filter(is_verified=True).count(),
            "unverified_hospitals": HospitalProfile.objects.filter(is_verified=False).count(),
            "total_requests": BloodRequest.objects.count(),
            "requests_by_status": {
                status_value: BloodRequest.objects.filter(status=status_value).count()
                for status_value, _ in BloodRequest.STATUS_CHOICES
            },
        }
        return Response(data)
