# promo/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import requests

# Django ORM bilan ishlash uchun django.setup() chaqirilishi kerak
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_name.settings")
django.setup()

# Django modellari import qilinadi
from .models import Promo, PromoEntry, PostbackRequest

app = FastAPI()

class SMSRequest(BaseModel):
    msisdn: str
    opi: int
    short_number: str
    message: str

def send_sms(msisdn, opi, short_number, custom_message):
    sms_api_url = "https://cp.vaspool.com/api/v1/sms/send?token=sUt1TCRZdhKTWXFLdOuy39JByFlx2"
    params = {
        'opi': opi,
        'msisdn': msisdn,
        'short_number': short_number,
        'message': custom_message
    }
    try:
        response = requests.get(sms_api_url, params=params)
        response.raise_for_status()
        return {"message": custom_message}
    except requests.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send SMS")

@app.get("/postback/")
async def postback_callback(sms_request: SMSRequest):
    msisdn = sms_request.msisdn
    opi = sms_request.opi
    short_number = sms_request.short_number
    text = sms_request.message

    if not (msisdn and opi and short_number and text):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Required parameters are missing")

    # Promo modelida promokod mavjudligini tekshirish
    promo = Promo.objects.filter(promo_text=text).first()
    if promo is None:
        custom_message = "Jo’natilgan Promokod noto’g’ri!"
        return send_sms(msisdn, opi, short_number, custom_message)

    # PromoEntry modelida ushbu promokod oldin ro'yxatdan o'tganligini tekshirish
    if PromoEntry.objects.filter(text=text, PostbackRequest__msisdn=msisdn).exists():
        custom_message = "Quyidagi Promokod avval ro’yxatdan o’tkazilgan!"
        return send_sms(msisdn, opi, short_number, custom_message)

    # PostbackRequest mavjudligini tekshirish va yangilash
    postback_request, created = PostbackRequest.objects.get_or_create(
        msisdn=msisdn,
        defaults={'opi': opi, 'short_number': short_number, 'sent_count': 1}
    )
    if not created:
        postback_request.sent_count += 1
        postback_request.save()

    # Yangi PromoEntry yaratish
    PromoEntry.objects.create(
        PostbackRequest=postback_request,
        text=text,
        created_at=datetime.now()
    )

    custom_message = (
        "Tabriklaymiz! Promokod qabul qilindi!\n"
        "\"Boriga baraka\" ko'rsatuvini har Juma soat 21:00 da Jonli efirda tomosha qiling!"
    )
    return send_sms(msisdn, opi, short_number, custom_message)
