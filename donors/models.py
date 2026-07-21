from django.conf import settings
from django.db import models


class DonorProfile(models.Model):
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Month 4: geolocation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_available = models.BooleanField(default=False)
    last_donation_date = models.DateField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_donations(self):
        return self.donations.filter(status=Donation.Status.COMPLETED).count()

    def __str__(self):
        return f"{self.user.username} ({self.blood_type})"


class Donation(models.Model):
    """
    A record of a donation, created as soon as a hospital matches
    a donor to a request, and tracked through to completion.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        DECLINED = 'declined', 'Declined'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
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
