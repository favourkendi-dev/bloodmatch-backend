from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import models
from .models import DonorProfile, Donation
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


class LeaderboardEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    blood_type = serializers.CharField()
    total_donations = serializers.IntegerField()


class LeaderboardView(APIView):
    """
    GET /api/donors/leaderboard/
    Returns top 20 donors by total completed donations.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Get top 20 donors by completed donations", responses=LeaderboardEntrySerializer(many=True))
    def get(self, request):
        donors = DonorProfile.objects.annotate(
            donation_count=models.Count('donations', filter=models.Q(donations__status=Donation.Status.COMPLETED))
        ).filter(donation_count__gt=0).order_by('-donation_count', '-updated_at')[:20]

        data = []
        for d in donors:
            data.append({
                'id': d.id,
                'username': d.user.username,
                'blood_type': d.blood_type,
                'total_donations': d.donation_count,
            })
        return Response(data)




class PublicDonorListView(generics.ListAPIView):
    """
    GET /api/donors/
    Public endpoint. Returns basic info about available donors.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DonorProfile.objects.filter(is_available=True).select_related('user')


class PublicDonorListView(generics.ListAPIView):
    """
    GET /api/donors/
    Public endpoint. Returns basic info about available donors.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DonorProfile.objects.filter(is_available=True).select_related('user')


class PublicDonorListView(generics.ListAPIView):
    """
    GET /api/donors/
    Public endpoint. Returns basic info about available donors.
    """
    serializer_class = DonorProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DonorProfile.objects.filter(is_available=True).select_related('user')
