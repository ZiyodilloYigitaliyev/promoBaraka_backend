# your_app/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import PostbackRequest, Notification
from .views import PostbackCallbackView  # Agar views dan send_sms chaqirsa


@shared_task
def send_notification_to_first_user_of_the_day():
    today = timezone.now().date()
    # Foydalanuvchidan birinchi marotaba promokod yuborganini aniqlash
    first_user = PostbackRequest.objects.filter(created_at__date=today).order_by('created_at').first()

    if first_user:
        notification = Notification.objects.filter(created_at__date=today).first()

        if notification:
            # Foydalanuvchiga SMS jo'natish
            postback_view = PostbackCallbackView()
            postback_view.send_sms(first_user.msisdn, first_user.short_number, notification.text)
            return f"Notification sent to {first_user.msisdn}"

    return "No users found or no notification to send."
