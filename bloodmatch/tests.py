from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from donors.models import DonorProfile
from hospitals.models import HospitalProfile

User = get_user_model()


class PublicStatsTests(APITestCase):
    """
    Test the public, unauthenticated stats endpoint used by the landing page.
    """

    def test_public_stats_accessible_without_auth(self):
        """Anyone, logged in or not, can hit this endpoint"""
        response = self.client.get('/api/public/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_public_stats_reflects_real_counts(self):
        """Counts match what's actually in the database"""
        donor_user = User.objects.create_user(username='donor1', password='pass12345', role='donor')
        DonorProfile.objects.create(user=donor_user, blood_type='O-')

        hospital_user = User.objects.create_user(username='hosp1', password='pass12345', role='hospital')
        HospitalProfile.objects.create(
            user=hospital_user,
            hospital_name='Test Hospital',
            registration_no='test-123',
            is_verified=True,
        )

        response = self.client.get('/api/public/stats/')
        self.assertEqual(response.data['total_donors'], 1)
        self.assertEqual(response.data['total_hospitals'], 1)
        self.assertEqual(response.data['verified_hospitals'], 1)
        self.assertEqual(response.data['blood_type_breakdown'], {'O-': 1})
