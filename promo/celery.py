from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Django konfiguratsiyasi faylini ko'rsating
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

app = Celery('promo')

# Django sozlamalarini Celery'ga yuklash
app.config_from_object('django.conf:settings', namespace='CELERY')

# Redis broker va natijalar backend konfiguratsiyasi
app.conf.broker_url = 'redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240'
app.conf.result_backend = 'redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240'
app.conf.broker_connection_retry_on_startup = True
# Celery'da vazifalarni avtomatik aniqlash
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Periodik vazifalarni sozlash
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from promo.tasks import reset_notification_sent
    sender.add_periodic_task(
        crontab(hour=12, minute=40),
        reset_notification_sent.s(),
    )



