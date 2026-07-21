from django.conf import settings
from django.db import models


class DonorProfile(models.Model):
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=False)
    last_donation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.blood_type})"


class Donation(models.Model):
    """
    A record of a single completed donation, created when a
    BloodRequest the donor was matched to is marked fulfilled.
    """
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='donations'
    )
    blood_request = models.ForeignKey(
        'requests_app.BloodRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_record'
    )
    donation_date = models.DateField(auto_now_add=True)
    units_donated = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.username} donated {self.units_donated} unit(s) on {self.donation_date}"
