from .models import PostbackRequest
from celery import Celery
from datetime import datetime

# Celeryni ulash
from .celery import app  # Bu yerda `celery.py` faylidan `app`ni import qilamiz.
@app.task
def run_daily_task():
    PostbackRequest.objects.update(notification_sent=False)
    now = datetime.now()
    print(f'Vazifa {now}da bajarildi.')
