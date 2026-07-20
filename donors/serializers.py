from rest_framework import serializers
from .models import DonorProfile


class DonorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = DonorProfile
        fields = [
            'id', 'username', 'blood_type', 'city',
            'is_available', 'last_donation_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

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
