import os
from celery import Celery
from celery.schedules import crontab
import ssl
from urllib.parse import urlparse

from conf import settings

# Django settings modulini o'rnatish
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

# Celery ilovasini yaratish
app = Celery('promo')

# Celery sozlamalarini o'qish (Django settings.py dan)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery uchun Redis URL
REDIS_URL = os.getenv('REDIS_URL', 'rediss://:pa87f4f6ec93d842280bf6cbe45917aa2ee10c47c81f4d478441e5bbad399aa53@ec2-54-72-43-199.eu-west-1.compute.amazonaws.com:7519')  # Heroku Redis URL (SSL)

# Redis ulanishi uchun SSL sozlamalari (Heroku Redis-da SSL talab qilinadi)
broker_url = REDIS_URL
parsed_url = urlparse(broker_url)

# SSL sozlamalarini faqat 'rediss://' URL uchun belgilash
if parsed_url.scheme == 'rediss':
    app.conf.update(
        CELERY_BROKER_URL=broker_url,
        CELERY_BROKER_OPTIONS={
            'ssl_cert_reqs': ssl.CERT_REQUIRED,  # SSL sertifikatini talab qilish
            'ssl_ca_certs': None,  # Heroku uchun bu parametr talab qilinmaydi
            'ssl_keyfile': None,  # Xususiy kalit (Kerak emas)
            'ssl_certfile': None  # Sertifikat (Kerak emas)
        }
    )
else:
    # Agar SSL ishlatilmasa, oddiy Redis ulanishi
    app.conf.update(
        CELERY_BROKER_URL=broker_url
    )

# Tasklar va Django app'larini Celery bilan ulash
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery tasklari uchun qo'llanmalar
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Celery Beat uchun sozlash (optional)
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Har 1 daqiqada ishga tushadigan taskni misol qilish
    from promo.tasks import test_task
    sender.add_periodic_task(
        crontab(minute='*/1'),  # Har 1 daqiqada test_task ni ishga tushurish
        test_task.s(),
        name='Test task'
    )

# Celery ilovasini eksport qilish (Django settings.py faylida ishlatiladi)
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

