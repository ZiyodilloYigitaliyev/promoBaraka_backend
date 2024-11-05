from promo.celery import shared_task
from .models import PostbackRequest

@shared_task
def reset_notification_status():
    # notification_sent maydonini har kuni 00:00 da False ga o'zgartiradi
    PostbackRequest.objects.all().update(notification_sent=False)
