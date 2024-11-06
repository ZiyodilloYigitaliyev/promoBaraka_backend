from celery import shared_task
from django.utils import timezone
from .models import PostbackRequest

@shared_task
def reset_notification_sent():
    # Filtrlash: faqat `True` bo'lgan qiymatlarni yangilash
    PostbackRequest.objects.filter(notification_sent=True).update(notification_sent=False)
