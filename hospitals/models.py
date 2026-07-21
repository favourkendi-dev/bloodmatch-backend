from django.conf import settings
from django.db import models
from django.utils import timezone


class HospitalProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    hospital_name = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)

    # Month 3: Hospital verification documentation
    registration_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Official hospital registration or license number"
    )
    license_document = models.FileField(
        upload_to='hospital_licenses/%Y/%m/',
        blank=True,
        null=True,
        help_text="Upload hospital license document"
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hospitals_verified'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.hospital_name or self.user.username

    def verify(self, admin_user):
        """
        Mark this hospital as verified by the given admin user.
        Updates is_verified, verified_by, and verified_at.
        """
        self.is_verified = True
        self.verified_by = admin_user
        self.verified_at = timezone.now()
        self.save()

    def unverify(self):
        """
        Remove verification status from this hospital.
        """
        self.is_verified = False
        self.verified_by = None
        self.verified_at = None
        self.save()
