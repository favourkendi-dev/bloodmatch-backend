from rest_framework import serializers
from .models import DonorProfile, Donation


class DonorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    total_donations = serializers.IntegerField(read_only=True)

    class Meta:
        model = DonorProfile
        fields = [
            'id', 'username', 'blood_type', 'city',
            'is_available', 'last_donation_date',
            'date_of_birth', 'gender', 'total_donations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_donations', 'created_at', 'updated_at']

    def validate(self, data):
        # Merge incoming data with existing instance values (for PATCH requests)
        blood_type = data.get('blood_type', getattr(self.instance, 'blood_type', ''))
        city = data.get('city', getattr(self.instance, 'city', ''))
        is_available = data.get('is_available', getattr(self.instance, 'is_available', False))
        if is_available and (not blood_type or not city):
            raise serializers.ValidationError(
                "Complete your blood type and city before marking yourself available."
            )
        return data


class DonationSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='blood_request.hospital.hospital_name', read_only=True, default=None)
    blood_type = serializers.CharField(source='blood_request.blood_type', read_only=True, default=None)

    class Meta:
        model = Donation
        fields = [
            'id', 'status', 'blood_request', 'hospital_name', 'blood_type',
            'donation_date', 'units_donated', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'donation_date', 'created_at']
