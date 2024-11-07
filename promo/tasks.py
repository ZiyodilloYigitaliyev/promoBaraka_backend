from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from .models import PostbackRequest

# Bu sizning har kuni soat 16:40 da bajariladigan vazifangiz
@periodic_task(run_every=crontab(hour=16, minute=40))
def reset_notification_sent():
    # Filtrlash: faqat `True` bo'lgan qiymatlarni yangilash
    PostbackRequest.objects.filter(notification_sent=True).update(notification_sent=False)
    print("reset_notification_sent task ishladi")