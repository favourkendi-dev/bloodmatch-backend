from rest_framework import serializers
from .models import BloodRequest


class BloodRequestSerializer(serializers.ModelSerializer):
    hospital_name = serializers.CharField(source='hospital.hospital_name', read_only=True)

    class Meta:
        model = BloodRequest
        fields = [
            'id', 'hospital_name', 'blood_type', 'units_needed',
            'urgency', 'city', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MatchedDonorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source='user.username')
    blood_type = serializers.CharField()
    city = serializers.CharField()
    phone_number = serializers.CharField(source='user.phone_number')
