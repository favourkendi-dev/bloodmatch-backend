from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import HospitalProfile
from .serializers import HospitalProfileSerializer


class MyHospitalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = HospitalProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = HospitalProfile.objects.get_or_create(user=self.request.user)
        return profile
