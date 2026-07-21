from django.db import models
from django.conf import settings


class Message(models.Model):
    """
    A message sent between a donor and a hospital regarding a specific blood request.
    Only the hospital owner and the matched donor can access messages for a request.
    """
    blood_request = models.ForeignKey(
        'requests_app.BloodRequest',
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="The blood request this message belongs to"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent this message"
    )
    content = models.TextField(
        help_text="Message content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the recipient has read this message"
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} on request #{self.blood_request.id}"

    def mark_as_read(self):
        """
        Mark this message as read by the recipient.
        """
        if not self.is_read:
            self.is_read = True
            self.save()
