from django.conf import settings
from django.db import models


class HospitalProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    hospital_name = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # geolocation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    contact_phone = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)

    # verification documents and audit
    registration_no = models.CharField(max_length=100, blank=True, unique=True, null=True)
    license_document = models.FileField(upload_to='hospital_licenses/', blank=True, null=True)
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
