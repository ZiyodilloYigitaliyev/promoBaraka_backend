from django.db import models

class SMSRequest(models.Model):
    opi = models.CharField(max_length=255)
    msisdn = models.CharField(max_length=15)  # Телефон рақами
    short_number = models.CharField(max_length=10)  # Қисқа рақам
    reqid = models.CharField(max_length=255, unique=True)  # Сўров ID
    result = models.TextField()  # Натижа
    created_at = models.DateTimeField(auto_now_add=True)  # Вақти
