from promo.models import PostbackRequest
from datetime import datetime

# Celeryni ulash
from conf.celery import app  # Bu yerda `celery.py` faylidan `app`ni import qilamiz.
@app.task
def run_daily_task():
    PostbackRequest.objects.update(notification_sent=False)
    now = datetime.now()
    print(f'Vazifa {now}da bajarildi.')

from celery import shared_task

@app.task
def test_task():
    print("Test task is running!")