from django.db import models
from django.conf import settings


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        REQUEST_CREATED = 'request_created', 'Request Created'
        REQUEST_MATCHED = 'request_matched', 'Request Matched'
        REQUEST_FULFILLED = 'request_fulfilled', 'Request Fulfilled'
        REQUEST_CANCELLED = 'request_cancelled', 'Request Cancelled'
        HOSPITAL_VERIFIED = 'hospital_verified', 'Hospital Verified'
        MESSAGE = 'message', 'New Message'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {'read' if self.is_read else 'unread'}"
