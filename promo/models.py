from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.apps import apps


class PostbackRequest(models.Model):
    msisdn = models.CharField(max_length=15)  # Abonentning telefon raqami
    opi = models.IntegerField()  # Operator ID (22, 23 yoki 27)
    short_number = models.CharField(max_length=10)  # Qisqa raqam (masalan, 7500)
    sent_count = models.IntegerField(default=0)
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
    notification_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.short_number} - {self.reqid}"


class Promo(models.Model):
    promo_text = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.promo_text


def get_default_date():
    NotificationDaily = apps.get_model('promo', 'NotificationDaily')
    try:
        last_notification = NotificationDaily.objects.latest('date')
        return last_notification.date + timedelta(days=1)
    except NotificationDaily.DoesNotExist:
        return timezone.now().date()
    except Exception as e:
        # Agar boshqa xatolik yuz bersa, hozirgi sanani qaytaradi
        return timezone.now().date()

class NotificationDaily(models.Model):
    date = models.DateField(default=get_default_date)
    text1 = models.TextField(null=True, blank=True)
    text2 = models.TextField(null=True, blank=True)
    text3 = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.date}"

    class Meta:
        # latest() metodida "date" maydoni asos sifatida ishlatiladi
        get_latest_by = 'date'



