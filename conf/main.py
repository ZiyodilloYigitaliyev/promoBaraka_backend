# fastapi_app/main.py
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import datetime
import os
from dotenv import load_dotenv

from conf.settings import BASE_DIR

app = FastAPI()
scheduler = BackgroundScheduler()
load_dotenv(os.path.join(BASE_DIR, '.env'))
# Django API URL manzili
DJANGO_API_URL = os.getenv("DJANGO_API_URL")  # Django API URL manzilini o'zingizga moslang

# Har kuni yuboriladigan vazifa
def send_daily_request():
    try:
        response = requests.get(DJANGO_API_URL, params={"message": "Har kunlik so'rov yuborildi"})
        if response.status_code == 200:
            print(f"{datetime.datetime.now()}: So'rov muvaffaqiyatli yuborildi")
        else:
            print(f"{datetime.datetime.now()}: Xato - Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"{datetime.datetime.now()}: So'rovda xatolik: {e}")


@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(send_daily_request, 'cron', hour=11, minute=0)  # Soat ishga tushadi
    scheduler.start()

# Ilova yopilganda scheduler ham to'xtaydi
@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

# Test uchun asosiy sahifa
@app.get("/")
async def root():
    return {"message": "FastAPI va Apscheduler ilovasi ishga tushdi"}
