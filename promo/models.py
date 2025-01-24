from django.db import models
from django.utils import timezone
import pytz

class PostbackRequest(models.Model):
    msisdn = models.CharField(max_length=15)  # Abonentning telefon raqami
    opi = models.IntegerField()  # Operator ID (22, 23 yoki 27)
    short_number = models.CharField(max_length=10)  # Qisqa raqam (masalan, 7500)
    sent_count = models.IntegerField(default=0)
    notification_sent = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.msisdn} - {self.short_number}"


class PromoEntry(models.Model):
    postback_request = models.ForeignKey(PostbackRequest, on_delete=models.CASCADE)
    text = models.TextField(unique=True)  # Abonentdan kelgan xabar
    created_at = models.DateTimeField()  # Ma'lumotlar qo'shilgan vaqt
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.text
class QueryLog(models.Model):
    msisdn = models.CharField(max_length=20, null=True, blank=True)
    opi = models.CharField(max_length=50, null=True, blank=True)
    short_number = models.CharField(max_length=10, null=True, blank=True)
    reqid = models.CharField(max_length=50, null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.short_number} - {self.reqid}"

class Promo(models.Model):
    promo_text = models.CharField(max_length=25, unique=True)

    def __str__(self):
        return self.promo_text


class Notification(models.Model):
    date = models.DateField()
    opi = models.IntegerField()  # Operator ID (22, 23 yoki 27)
    text = models.TextField()  # Xabar matni

    def __str__(self):
        return f"Notification for {self.date}"






# class PromoCode(models.Model):
#     code = models.CharField(max_length=50)