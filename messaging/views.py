from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from .models import Message
from .serializers import MessageSerializer
from requests_app.models import BloodRequest
from notifications.models import Notification


class MessageListCreateView(generics.ListCreateAPIView):
    """
    GET /api/messages/?blood_request=<id>  → List messages for a request
    POST /api/messages/                    → Send a new message on a request

    Only the hospital owner or the matched donor can view/send.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        blood_request_id = self.request.query_params.get('blood_request')

        if not blood_request_id:
            return Message.objects.none()

        try:
            blood_request = BloodRequest.objects.get(pk=blood_request_id)
        except BloodRequest.DoesNotExist:
            return Message.objects.none()

        # Only allow the hospital owner or the matched donor
        is_hospital = (
            hasattr(user, 'hospital_profile')
            and blood_request.hospital.user == user
        )
        is_matched_donor = (
            hasattr(user, 'donor_profile')
            and blood_request.matched_donor
            and blood_request.matched_donor.user == user
        )

        if not (is_hospital or is_matched_donor):
            raise PermissionDenied("You are not a participant in this request.")

        return Message.objects.filter(blood_request=blood_request)

    def perform_create(self, serializer):
        user = self.request.user
        blood_request_id = self.request.data.get('blood_request')

        if not blood_request_id:
            raise PermissionDenied("blood_request is required.")

        try:
            blood_request = BloodRequest.objects.get(pk=blood_request_id)
        except BloodRequest.DoesNotExist:
            raise NotFound("Blood request not found.")

        # Same permission check
        is_hospital = (
            hasattr(user, 'hospital_profile')
            and blood_request.hospital.user == user
        )
        is_matched_donor = (
            hasattr(user, 'donor_profile')
            and blood_request.matched_donor
            and blood_request.matched_donor.user == user
        )

        if not (is_hospital or is_matched_donor):
            raise PermissionDenied("You are not a participant in this request.")

        message = serializer.save(sender=user, blood_request=blood_request)

        # Create notification for the other party
        self._create_message_notification(message, blood_request, user)

        return message

    def _create_message_notification(self, message, blood_request, sender):
        """
        Create a notification for the recipient when a message is sent.
        """
        # Determine who the recipient is
        if hasattr(sender, 'hospital_profile'):
            # Hospital sent message → notify donor
            recipient = blood_request.matched_donor.user if blood_request.matched_donor else None
        elif hasattr(sender, 'donor_profile'):
            # Donor sent message → notify hospital
            recipient = blood_request.hospital.user
        else:
            recipient = None

        if recipient:
            Notification.objects.create(
                user=recipient,
                notification_type=Notification.NotificationType.MESSAGE,
                message=f"New message from {sender.username} regarding blood request #{blood_request.id}"
            )


class MarkMessageAsReadView(APIView):
    """
    POST /api/messages/<id>/read/
    Mark a specific message as read. Only the recipient (non-sender) can do this.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            message = Message.objects.get(pk=pk)
        except Message.DoesNotExist:
            raise NotFound("Message not found.")

        # Only the recipient should mark as read
        if message.sender == request.user:
            return Response(
                {"detail": "You cannot mark your own message as read."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify this user is a participant in the request
        blood_request = message.blood_request
        is_hospital = (
            hasattr(request.user, 'hospital_profile')
            and blood_request.hospital.user == request.user
        )
        is_matched_donor = (
            hasattr(request.user, 'donor_profile')
            and blood_request.matched_donor
            and blood_request.matched_donor.user == request.user
        )

        if not (is_hospital or is_matched_donor):
            raise PermissionDenied("You are not a participant in this conversation.")

        message.mark_as_read()
        return Response({"detail": "Message marked as read."})


class UnreadMessageCountView(APIView):
    """
    GET /api/messages/unread_count/
    Returns the number of unread messages for the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        count = Message.objects.filter(
            blood_request__in=self._get_user_requests(user),
            is_read=False
        ).exclude(sender=user).count()

        return Response({"unread_count": count})

    def _get_user_requests(self, user):
        """
        Helper to get all blood requests this user is involved in.
        """
        if hasattr(user, 'hospital_profile'):
            return BloodRequest.objects.filter(hospital=user.hospital_profile)
        elif hasattr(user, 'donor_profile'):
            return BloodRequest.objects.filter(matched_donor=user.donor_profile)
        return BloodRequest.objects.none()
