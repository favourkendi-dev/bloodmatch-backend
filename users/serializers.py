from rest_framework import serializers
from django.contrib.auth import get_user_model
from donors.models import DonorProfile
from hospitals.models import HospitalProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    blood_type = serializers.ChoiceField(
        choices=DonorProfile.BLOOD_TYPE_CHOICES, required=False, allow_blank=True
    )
    hospital_name = serializers.CharField(required=False, allow_blank=True)
    registration_no = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role', 'phone_number',
            'blood_type', 'hospital_name', 'registration_no',
        ]

    def create(self, validated_data):
        blood_type = validated_data.pop('blood_type', '')
        hospital_name = validated_data.pop('hospital_name', '')
        registration_no = validated_data.pop('registration_no', '')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'donor'),
            phone_number=validated_data.get('phone_number', ''),
        )

        if user.role == 'donor':
            DonorProfile.objects.create(
                user=user,
                blood_type=blood_type,
            )
        elif user.role == 'hospital':
            HospitalProfile.objects.create(
                user=user,
                hospital_name=hospital_name,
                registration_no=registration_no,
                contact_phone=validated_data.get('phone_number', ''),
            )

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone_number', 'date_joined']
