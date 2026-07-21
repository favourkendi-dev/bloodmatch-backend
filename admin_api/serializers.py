from rest_framework import serializers
from hospitals.models import HospitalProfile
from donors.models import DonorProfile
from requests_app.models import BloodRequest


class AdminHospitalSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    verified_by_username = serializers.CharField(source='verified_by.username', read_only=True, default=None)

    class Meta:
        model = HospitalProfile
        fields = [
            'id', 'username', 'email', 'hospital_name',
            'city', 'contact_phone', 'registration_no', 'license_document',
            'is_verified', 'verified_by_username', 'verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'registration_no', 'license_document',
            'is_verified', 'verified_by_username', 'verified_at',
            'created_at', 'updated_at'
        ]


class AdminDonorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    total_donations = serializers.IntegerField(read_only=True)

    class Meta:
        model = DonorProfile
        fields = [
            'id', 'username', 'email', 'blood_type',
            'city', 'is_available', 'last_donation_date',
            'date_of_birth', 'gender', 'total_donations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_donations', 'created_at', 'updated_at']


class AdminBloodRequestSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)
    matched_donor_username = serializers.CharField(source='matched_donor.user.username', read_only=True, default=None)

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'hospital_name', 'blood_type', 'units_needed',
            'urgency', 'city', 'status', 'donor_confirmed',
            'matched_donor_username', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
