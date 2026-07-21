from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from donors.models import DonorProfile, Donation
from hospitals.models import HospitalProfile
from .models import BloodRequest
from .compatibility import get_compatible_donor_types
from .geo import calculate_distance_km

User = get_user_model()


class CompatibilityTests(TestCase):
    """
    Test blood type compatibility logic.
    """

    def test_o_negative_recipient(self):
        """O- can only receive O-"""
        types = get_compatible_donor_types('O-')
        self.assertEqual(types, ['O-'])

    def test_ab_positive_recipient(self):
        """AB+ can receive from anyone"""
        types = get_compatible_donor_types('AB+')
        self.assertEqual(set(types), {'O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'})


class GeoDistanceTests(TestCase):
    """
    Test distance calculation between two points.
    """

    def test_nairobi_cbd_to_westlands(self):
        """Test known distance between two Nairobi points"""
        lat1, lon1 = -1.286389, 36.817223
        lat2, lon2 = -1.267389, 36.811223
        distance = calculate_distance_km(lat1, lon1, lat2, lon2)
        self.assertGreater(distance, 0)
        self.assertLess(distance, 10)


class BloodRequestAPITests(APITestCase):
    """
    Test blood request API endpoints.
    """

    def setUp(self):
        self.client = APIClient()

        self.hospital_user = User.objects.create_user(
            username='testhospital',
            password='testpass123',
            email='hospital@test.com'
        )
        self.hospital_profile = HospitalProfile.objects.create(
            user=self.hospital_user,
            hospital_name='Test Hospital',
            city='Nairobi',
            is_verified=True
        )

        self.donor_user = User.objects.create_user(
            username='testdonor',
            password='testpass123',
            email='donor@test.com'
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_type='O-',
            city='Nairobi',
            is_available=True
        )

        from rest_framework_simplejwt.tokens import RefreshToken
        h_refresh = RefreshToken.for_user(self.hospital_user)
        self.hospital_token = str(h_refresh.access_token)

        d_refresh = RefreshToken.for_user(self.donor_user)
        self.donor_token = str(d_refresh.access_token)

    def test_create_blood_request(self):
        """Hospital can create a blood request"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        data = {
            'blood_type': 'O-',
            'units_needed': 2,
            'urgency': 'urgent',
            'city': 'Nairobi',
            'notes': 'Test request'
        }
        response = self.client.post('/api/requests/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['blood_type'], 'O-')
        self.assertEqual(response.data['status'], 'open')

    def test_only_hospital_can_create_request(self):
        """Donor cannot create a blood request"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.donor_token)
        data = {
            'blood_type': 'O-',
            'units_needed': 1,
            'urgency': 'normal',
            'city': 'Nairobi'
        }
        response = self.client.post('/api/requests/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_match_donors_returns_compatible_donors(self):
        """Matching endpoint returns compatible donors"""
        request = BloodRequest.objects.create(
            hospital=self.hospital_profile,
            blood_type='O-',
            units_needed=1,
            urgency='normal',
            city='Nairobi',
            status='open'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        response = self.client.get('/api/requests/' + str(request.id) + '/matches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        usernames = [d['username'] for d in response.data]
        self.assertIn('testdonor', usernames)

    def test_select_donor_creates_donation(self):
        """Selecting a donor creates a pending donation"""
        request = BloodRequest.objects.create(
            hospital=self.hospital_profile,
            blood_type='O-',
            units_needed=1,
            urgency='normal',
            city='Nairobi',
            status='open'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        data = {'donor_id': self.donor_profile.id}
        response = self.client.post(
            '/api/requests/' + str(request.id) + '/select_donor/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

        donation = Donation.objects.filter(blood_request=request).first()
        self.assertIsNotNone(donation)
        self.assertEqual(donation.status, Donation.Status.PENDING)

    def test_donor_can_accept_request(self):
        """Matched donor can accept a request"""
        request = BloodRequest.objects.create(
            hospital=self.hospital_profile,
            blood_type='O-',
            units_needed=1,
            urgency='normal',
            city='Nairobi',
            status='in_progress',
            matched_donor=self.donor_profile
        )
        Donation.objects.create(
            donor=self.donor_profile,
            blood_request=request,
            units_donated=1,
            status=Donation.Status.PENDING
        )
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.donor_token)
        response = self.client.post('/api/requests/' + str(request.id) + '/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['donor_confirmed'])

        donation = Donation.objects.get(blood_request=request)
        self.assertEqual(donation.status, Donation.Status.ACCEPTED)

    def test_fulfill_request_completes_donation(self):
        """Fulfilling request marks donation completed and updates donor stats"""
        request = BloodRequest.objects.create(
            hospital=self.hospital_profile,
            blood_type='O-',
            units_needed=1,
            urgency='normal',
            city='Nairobi',
            status='in_progress',
            matched_donor=self.donor_profile,
            donor_confirmed=True
        )
        Donation.objects.create(
            donor=self.donor_profile,
            blood_request=request,
            units_donated=1,
            status=Donation.Status.ACCEPTED
        )
        initial_donations = self.donor_profile.total_donations

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        response = self.client.post('/api/requests/' + str(request.id) + '/fulfill/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'fulfilled')

        self.donor_profile.refresh_from_db()
        self.assertEqual(self.donor_profile.total_donations, initial_donations + 1)
        self.assertIsNotNone(self.donor_profile.last_donation_date)
