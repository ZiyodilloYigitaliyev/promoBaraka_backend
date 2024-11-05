from rest_framework import serializers
from .models import *


class PromoEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoEntry
        fields = '__all__'

class PostbackRequestSerializer(serializers.ModelSerializer):
    entries = PromoEntrySerializer(many=True, read_only=True)
    class Meta:
        model = PostbackRequest
        fields = '__all__'

# class PromoEntrySerializerSent(serializers.ModelSerializer):
#     class Meta:
#         model = PromoEntry
#         fields = ['text', 'created_at']

class PostbackRequestSerializerSent(serializers.ModelSerializer):
    promos = PromoEntrySerializer(many=True, read_only=True, source='promoentry_set')  # promo ma'lumotlari

    class Meta:
        model = PostbackRequest
        fields = ['opi', 'msisdn', 'short_number', 'sent_count', 'promos']



class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promo
        fields = ['promo_text']

