from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import DonorProfile
from .serializers import DonorProfileSerializer, DonationSerializer


class MyDonorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = DonorProfile.objects.get_or_create(user=self.request.user)
        return profile


class MyDonationHistoryView(generics.ListAPIView):
    """
    GET /api/donors/donations/
    Donor-only. Returns this donor's full donation history, most recent first.
    """
    serializer_class = DonationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile, created = DonorProfile.objects.get_or_create(user=self.request.user)
        return profile.donations.all().order_by('-donation_date')
