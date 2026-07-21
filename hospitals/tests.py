from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import HospitalProfile

User = get_user_model()


class HospitalVerificationTests(APITestCase):
    """
    Test hospital verification workflow.
    """

    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass',
            email='admin@test.com',
            is_staff=True
        )
        self.hospital_user = User.objects.create_user(
            username='hospital',
            password='hospitalpass',
            email='hospital@test.com'
        )
        self.hospital_profile = HospitalProfile.objects.create(
            user=self.hospital_user,
            hospital_name='Unverified Hospital',
            city='Nairobi',
            is_verified=False,
            registration_no='REG123456'
        )

        from rest_framework_simplejwt.tokens import RefreshToken
        admin_refresh = RefreshToken.for_user(self.admin_user)
        self.admin_token = str(admin_refresh.access_token)

        hospital_refresh = RefreshToken.for_user(self.hospital_user)
        self.hospital_token = str(hospital_refresh.access_token)

    def test_admin_can_verify_hospital(self):
        """Admin can verify a hospital"""
        self.assertFalse(self.hospital_profile.is_verified)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token)
        response = self.client.post(
            '/api/hospitals/admin/verify/' + str(self.hospital_profile.id) + '/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.hospital_profile.refresh_from_db()
        self.assertTrue(self.hospital_profile.is_verified)
        self.assertEqual(self.hospital_profile.verified_by, self.admin_user)
        self.assertIsNotNone(self.hospital_profile.verified_at)

    def test_non_admin_cannot_verify(self):
        """Regular user cannot verify a hospital"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        response = self.client.post(
            '/api/hospitals/admin/verify/' + str(self.hospital_profile.id) + '/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_hospital_can_update_registration(self):
        """Hospital can update their own registration number"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        data = {'registration_no': 'NEWREG789'}
        response = self.client.patch('/api/hospitals/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_no'], 'NEWREG789')

    def test_public_list_shows_only_verified(self):
        """Public hospital list only shows verified hospitals"""
        verified_hospital = User.objects.create_user(
            username='verified_hospital',
            password='pass123'
        )
        HospitalProfile.objects.create(
            user=verified_hospital,
            hospital_name='Verified Hospital',
            city='Nairobi',
            is_verified=True
        )

        response = self.client.get('/api/hospitals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [h['hospital_name'] for h in response.data]
        self.assertIn('Verified Hospital', names)
        self.assertNotIn('Unverified Hospital', names)
