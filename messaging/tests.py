from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from donors.models import DonorProfile
from hospitals.models import HospitalProfile
from requests_app.models import BloodRequest
from messaging.models import Message
from notifications.models import Notification

User = get_user_model()


class MessageTests(APITestCase):
    """
    Test messaging between donor and hospital.
    """

    def setUp(self):
        self.client = APIClient()

        self.hospital_user = User.objects.create_user(
            username='hospital',
            password='pass123'
        )
        self.hospital_profile = HospitalProfile.objects.create(
            user=self.hospital_user,
            hospital_name='Test Hospital',
            city='Nairobi',
            is_verified=True
        )

        self.donor_user = User.objects.create_user(
            username='donor',
            password='pass123'
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            blood_type='O-',
            city='Nairobi',
            is_available=True
        )

        self.request = BloodRequest.objects.create(
            hospital=self.hospital_profile,
            blood_type='O-',
            units_needed=1,
            urgency='normal',
            city='Nairobi',
            status='in_progress',
            matched_donor=self.donor_profile
        )

        from rest_framework_simplejwt.tokens import RefreshToken
        h_refresh = RefreshToken.for_user(self.hospital_user)
        self.hospital_token = str(h_refresh.access_token)

        d_refresh = RefreshToken.for_user(self.donor_user)
        self.donor_token = str(d_refresh.access_token)

    def test_hospital_can_send_message(self):
        """Hospital can send message to matched donor"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        data = {
            'blood_request': self.request.id,
            'content': 'Please come tomorrow at 10 AM'
        }
        response = self.client.post('/api/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Please come tomorrow at 10 AM')
        self.assertEqual(response.data['sender_username'], 'hospital')

    def test_donor_can_send_message(self):
        """Donor can send message to hospital"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.donor_token)
        data = {
            'blood_request': self.request.id,
            'content': 'I will be there'
        }
        response = self.client.post('/api/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_message_creates_notification(self):
        """Sending a message creates a notification for recipient"""
        initial_count = Notification.objects.filter(user=self.donor_user).count()

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        data = {
            'blood_request': self.request.id,
            'content': 'Please confirm your arrival'
        }
        response = self.client.post('/api/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notification_count = Notification.objects.filter(user=self.donor_user).count()
        self.assertEqual(notification_count, initial_count + 1)

    def test_unmatched_user_cannot_message(self):
        """A user not involved in the request cannot send messages"""
        other_user = User.objects.create_user(username='other', password='pass123')
        DonorProfile.objects.create(user=other_user, blood_type='A+', city='Nairobi')

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(other_user)
        token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        data = {
            'blood_request': self.request.id,
            'content': 'I want to help'
        }
        response = self.client.post('/api/messages/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mark_message_as_read(self):
        """Recipient can mark message as read"""
        msg = Message.objects.create(
            blood_request=self.request,
            sender=self.hospital_user,
            content='Test message'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.donor_token)
        response = self.client.post('/api/messages/' + str(msg.id) + '/read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_sender_cannot_mark_own_message_read(self):
        """Sender cannot mark their own message as read"""
        msg = Message.objects.create(
            blood_request=self.request,
            sender=self.hospital_user,
            content='Test message'
        )

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.hospital_token)
        response = self.client.post('/api/messages/' + str(msg.id) + '/read/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
