from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import DonorProfile
from .serializers import DonorProfileSerializer


class MyDonorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = DonorProfile.objects.get_or_create(user=self.request.user)
        return profile
