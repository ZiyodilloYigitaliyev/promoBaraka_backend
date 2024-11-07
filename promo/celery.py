from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from promo.tasks import run_daily_task  # run_daily_task taskini import qilamiz.
# Celery ilovasini yaratish
app = Celery('promo', broker='redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240')

# Celery konfiguratsiyasi
app.conf.update(
    result_backend='redis://:387f7018f82b855191fdc271aac03c6caccf9c90c044f861c56c2b6058aa927c@b94ca.openredis.io:18240',  # Redis backendni qo'llash
    timezone='Asia/Tashkent',  # O'zbekiston vaqti
    enable_utc=True,  # UTCni yoqish
)

# Periodik tasklarni yuklash uchun
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Har kuni soat 3:00da `run_daily_task`ni bajarish
    sender.add_periodic_task(
        {'hour': 16, 'minute': 15},  # 3:00 PMda ishlash
        run_daily_task.s(),  # Taskni chaqirish
        name='Har kuni soat 3:00da ishlovchi task'
    )
