from __future__ import absolute_import, unicode_literals
import os
from celery import Celery


# Django settings-ni to'g'ri yuklash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
# Celery ilovasini yaratish
app = Celery('promo')

# Celery konfiguratsiyasi
app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240'),  # Heroku Redis URL
    result_backend=os.getenv('REDIS_URL', 'redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240'),
    timezone='Asia/Tashkent',  # O'zbekiston vaqti
    enable_utc=True,  # UTCni yoqish
)

# Periodik tasklarni yuklash uchun
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from promo.tasks import run_daily_task
    sender.add_periodic_task(
        {'hour': 16, 'minute': 30},
        run_daily_task.s(),  # Taskni chaqirish
        name='Har kuni soat 3:00da ishlovchi task'
    )
