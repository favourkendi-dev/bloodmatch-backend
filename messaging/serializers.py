from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_type = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id',
            'blood_request',
            'sender',
            'sender_username',
            'sender_type',
            'content',
            'created_at',
            'is_read',
        ]
        read_only_fields = ['sender', 'created_at']

    def get_sender_type(self, obj):
        user = obj.sender
        if hasattr(user, 'donor_profile'):
            return 'donor'
        elif hasattr(user, 'hospital_profile'):
            return 'hospital'
        return 'unknown'
