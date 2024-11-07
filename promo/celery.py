from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

from conf import settings

# Django settings-ni to'g'ri yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
# Celery ilovasini yaratish
app = Celery('promo')

# Celery konfiguratsiyasi
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Boshqa kerakli sozlamalar (optional)
app.conf.beat_schedule = {
    'test-task': {
        'task': 'promo.tasks.test_task',
        'schedule': crontab(minute='*/1'),  # Har daqiqada ishlash
    }
}
# # Periodik tasklarni yuklash uchun
# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     from promo.tasks import run_daily_task
#     sender.add_periodic_task(
#         {'hour': 22, 'minute': 15},
#         run_daily_task.s(),  # Taskni chaqirish
#         name='Har kuni soat ishlovchi task'
#     )
