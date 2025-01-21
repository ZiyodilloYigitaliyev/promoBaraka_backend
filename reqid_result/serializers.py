from rest_framework import serializers
from .models import SMSRequest

class SMSRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSRequest
        fields = ['id', 'opi', 'msisdn', 'short_number', 'reqid', 'result', 'created_at']
