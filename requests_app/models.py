from django.conf import settings
from django.db import models
from hospitals.models import HospitalProfile


class BloodRequest(models.Model):
    BLOOD_TYPE_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    URGENCY_CHOICES = (
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    )

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    )

    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    matched_donor = models.ForeignKey(
        'donors.DonorProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_requests'
    )
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES)
    units_needed = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='normal')
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_type} x{self.units_needed} @ {self.hospital} ({self.status})"
