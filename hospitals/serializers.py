from rest_framework import serializers
from .models import HospitalProfile


class HospitalProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = HospitalProfile
        fields = [
            'id', 'username', 'hospital_name', 'city',
            'contact_phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
