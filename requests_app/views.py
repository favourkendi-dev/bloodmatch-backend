from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import BloodRequest
from .serializers import BloodRequestSerializer


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
