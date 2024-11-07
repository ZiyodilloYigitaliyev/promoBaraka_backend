from celery import shared_task
from django.utils import timezone
from .models import PostbackRequest

@shared_task
def reset_notification_sent():
    # Bu yerda notification_sent maydonini yangilash
    PostbackRequest.objects.update(notification_sent=False)
    print("notification_sent maydoni yangilandi.")
