from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from .models import HospitalProfile
from .serializers import HospitalProfileSerializer


class MyHospitalProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/hospitals/profile/  → View own hospital profile
    PATCH /api/hospitals/profile/ → Update own profile
    """
    serializer_class = HospitalProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = HospitalProfile.objects.get_or_create(user=self.request.user)
        return profile


class HospitalListView(generics.ListAPIView):
    """
    GET /api/hospitals/ → List all verified hospitals
    Public endpoint, no login required.
    """
    serializer_class = HospitalProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # Only show verified hospitals to the public
        return HospitalProfile.objects.filter(is_verified=True)


class AdminVerifyHospitalView(APIView):
    """
    POST /api/hospitals/admin/verify/<id>/
    Admin-only. Verifies a hospital and records who did it and when.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin users can verify hospitals.")

        try:
            hospital = HospitalProfile.objects.get(pk=pk)
        except HospitalProfile.DoesNotExist:
            raise NotFound("Hospital not found.")

        if hospital.is_verified:
            return Response(
                {"detail": "This hospital is already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hospital.verify(request.user)

        serializer = HospitalProfileSerializer(hospital)
        return Response(serializer.data)


class AdminUnverifyHospitalView(APIView):
    """
    POST /api/hospitals/admin/unverify/<id>/
    Admin-only. Removes verification from a hospital.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only admin users can unverify hospitals.")

        try:
            hospital = HospitalProfile.objects.get(pk=pk)
        except HospitalProfile.DoesNotExist:
            raise NotFound("Hospital not found.")

        if not hospital.is_verified:
            return Response(
                {"detail": "This hospital is not currently verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hospital.unverify()

        serializer = HospitalProfileSerializer(hospital)
        return Response(serializer.data)
