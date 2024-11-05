from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Django asosiy faylini ko'rsating
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

app = Celery('promo')

# Django sozlamalarini Celery'ga yuklash
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery'ning vazifalarni avtomatik yuklashi
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
