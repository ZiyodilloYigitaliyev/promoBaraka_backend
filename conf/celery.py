from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django settings modulini o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

# Celery ilovasini yaratish
app = Celery('conf')

# Django sozlamalaridan Celery konfiguratsiyasini import qilish
app.config_from_object('django.conf:settings', namespace='CELERY')

# Vazifalarni avtomatik aniqlash
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')