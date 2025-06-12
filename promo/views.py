import requests
import random
import chardet
from rest_framework.parsers import FileUploadParser
import json
from django.utils import timezone
import pytz
from django.db import transaction
from rest_framework import viewsets, status
from django.core.files.storage import default_storage
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncMonth
import calendar
from django.http import JsonResponse
from django.views import View
from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import timedelta, datetime
from rest_framework.viewsets import ViewSet
from .serializers import *
from django.db import IntegrityError
from django.db.models import Q
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ExcelUploadForm
from .models import NotificationDaily
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from datetime import date 
import logging
import pytz

logger = logging.getLogger(__name__)

def notification_sms(self, msisdn, opi, short_number):
    today = timezone.now().date()
    notification = NotificationDaily.objects.filter(date=today).first()

    if notification:
        # NotificationDaily modelidagi 3 matndan tasodifiy birini tanlab olamiz
        notification_message = random.choice([notification.text1, notification.text2, notification.text3])
        sms_api_url = "https://cp.vaspool.com/api/v1/sms/send?token=sUt1TCRZdhKTWXFLdOuy39JByFlx2"
        params = {
            'opi': opi,
            'msisdn': msisdn,
            'short_number': short_number,
            'message': notification_message
        }
        try:
            requests.get(sms_api_url, params=params)
        except requests.RequestException as e:
            print("Failed to send notification SMS:", e)
            
class PostbackCallbackView(APIView):
    permission_classes = [AllowAny]

    def send_sms(self, msisdn, opi, short_number, custom_message):
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
            return response
        except requests.RequestException as e:
            logger.exception("SMS yuborishda xatolik: %s", str(e))
            return None

    def get(self, request, *args, **kwargs):
        msisdn = request.query_params.get('msisdn')
        opi = request.query_params.get('opi')
        short_number = request.query_params.get('short_number')
        text = request.query_params.get('message')
        reqid = request.query_params.get('reqid')
        result = request.query_params.get('result')

        logger.info(f"Postback GET: msisdn={msisdn}, opi={opi}, short_number={short_number}, text={text}, reqid={reqid}, result={result}")

        if not msisdn or not opi or not short_number:
            return Response({"error": "Kerakli parametrlar yetarli emas!"}, status=status.HTTP_400_BAD_REQUEST)

        if short_number == "7500":
            if not text:
                return Response({"error": "Promokod (message) yo'q!"}, status=status.HTTP_400_BAD_REQUEST)

            promo = Promo.objects.filter(promo_text=text).first()
            if not promo:
                custom_message = "Jo’natilgan Promokod noto’g’ri!"
                self.send_sms(msisdn, opi, short_number, custom_message)
                return Response({"message": custom_message}, status=status.HTTP_200_OK)

            if PromoEntry.objects.filter(postback_request__msisdn=msisdn, text=text).exists():
                custom_message = "Quyidagi Promokod avval ro’yxatdan o’tkazilgan!"
                self.send_sms(msisdn, opi, short_number, custom_message)
                return Response({"message": custom_message}, status=status.HTTP_200_OK)

            postback_request, created = PostbackRequest.objects.get_or_create(
                msisdn=msisdn,
                defaults={'opi': opi, 'short_number': short_number, 'sent_count': 1}
            )
            if not created:
                postback_request.sent_count += 1
                postback_request.save()

            PromoEntry.objects.create(
                postback_request=postback_request,
                text=text,
                created_at=timezone.now()
            )

            success_message = (
                "Tabriklaymiz! Promokod qabul qilindi!\n"
                "\"Boriga baraka\" ko'rsatuvini har Juma soat 21:00 da Jonli efirda tomosha qiling!"
            )
            response = self.send_sms(msisdn, opi, short_number, success_message)
            if response:
                return Response({"message": success_message}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "SMS yuborishda muammo bo‘ldi!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif short_number == "07500":
            if not (reqid and result):
                return Response({
                    "error": "07500 uchun kerakli parametrlar yetarli emas!",
                    "missing_params": [p for p in ['reqid', 'result'] if not request.query_params.get(p)]
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                QueryLog.objects.create(
                    msisdn=msisdn,
                    opi=opi,
                    short_number=short_number,
                    reqid=reqid,
                    result=result
                )

                response_1 = self.send_sms(msisdn, opi, short_number, "Sizning arizangiz qabul qilindi, javob SMSni kuting.")
                response_2 = self.send_sms(msisdn, opi, short_number,
                    "Boriga Baraka Kapital Shou uchun kodingiz qabul qilindi. "
                    "Efir Zo'r TV kanalida har juma soat 20.20 da. "
                    "Spasibo! Kod prinyat. Sledite za efirom na Zo'r TV kanale kajduyu pyatnitsu v 20.20. "
                    "Tel: 998(78)147-78-89."
                )

                tashkent_now = timezone.now().astimezone(pytz.timezone("Asia/Tashkent"))
                today = tashkent_now.date()

                notification = NotificationDaily.objects.filter(date=today).first()
                if not notification:
                    return Response({"error": "Bugungi Notification mavjud emas!"}, status=404)

                texts = [t for t in [notification.text1, notification.text2, notification.text3] if t]
                if not texts:
                    return Response({"error": "Notification matni topilmadi!"}, status=404)

                notification_message = random.choice(texts)
                response_3 = self.send_sms(msisdn, opi, short_number, notification_message)

                if all([response_1, response_2, response_3]):
                    return Response({"message": "Barcha SMS yuborildi!"}, status=status.HTTP_200_OK)
                else:
                    errors = []
                    if not response_1:
                        errors.append("SMS 1 yuborilmadi!")
                    if not response_2:
                        errors.append("SMS 2 yuborilmadi!")
                    if not response_3:
                        errors.append("Notification SMS yuborilmadi!")
                    return Response({"error": "Ba'zi SMS yuborilmadi", "details": errors}, status=500)

            except Exception as e:
                logger.exception("Postback (07500) xatolik: %s", str(e))
                return Response({"error": "Server xatoligi", "details": str(e)}, status=500)

        else:
            return Response({"error": f"Noma'lum short_number: {short_number}"}, status=400)



#     ********************* Monthly date *************************
class PromoMonthlyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        # Agar month va year parametrlar kiritilgan bo'lsa, o'sha oyni filtrlaymiz
        if month and year:
            try:
                month = int(month)
                year = int(year)

                if month < 1 or month > 12:
                    raise ValueError("Month must be between 1 and 12.")
                if year < 1900:
                    raise ValueError("Year must be greater than 1900.")

                # Oylik sana oralig'ini yaratish
                start_date = timezone.make_aware(timezone.datetime(year, month, 1))
                end_date = timezone.make_aware(
                    timezone.datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59))

                # Berilgan oy uchun PromoEntry yozuvlarini olish
                promos_in_month = PromoEntry.objects.filter(
                    created_at__range=(start_date, end_date)
                ).select_related('postback_request')  # postback_request bilan bog'lash

                # PostbackRequest'ni promos bilan bog'lash
                promos_grouped = {}
                for entry in promos_in_month:
                    postback_request = entry.postback_request  # postback_request maydoni bilan bog'lanish
                    if postback_request.msisdn not in promos_grouped:
                        promos_grouped[postback_request.msisdn] = {
                            "sent_count": 0,
                            "promos": []
                        }

                    # sent_countni har bir foydalanuvchi uchun orttirish
                    promos_grouped[postback_request.msisdn]["sent_count"] += 1
                    # Har bir promo kodni promos ro'yxatiga qo'shish
                    promos_grouped[postback_request.msisdn]["promos"].append({
                        "id": entry.id,
                        "text": entry.text,
                        "created_at": entry.created_at.isoformat()
                    })
                # Natija tuzish
                result = {
                    "month": calendar.month_name[month].lower(),
                    "promos": promos_grouped,
                }

            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Agar month va year kiritilmagan bo'lsa, barcha oylardagi ma'lumotlarni qaytarish
        else:
            # Barcha oylardagi ma'lumotlarni olish
            entries = PromoEntry.objects.annotate(month=TruncMonth('created_at')).values('month').distinct()

            result = {}
            for entry in entries:
                month = entry['month']
                month_name = month.strftime("%B").lower()
                start_date = timezone.make_aware(timezone.datetime(month.year, month.month, 1))
                end_date = timezone.make_aware(
                    timezone.datetime(month.year, month.month, calendar.monthrange(month.year, month.month)[1], 23, 59,
                                      59))

                # Promolarni olish
                promos_in_month = PromoEntry.objects.filter(
                    created_at__range=(start_date, end_date)
                ).select_related('postback_request')

                # Promolarni guruhlash
                promos_grouped = {}
                for entry in promos_in_month:
                    postback_request = entry.postback_request  # postback_request maydoni bilan bog'lanish
                    if postback_request.msisdn not in promos_grouped:
                        promos_grouped[postback_request.msisdn] = {
                            "sent_count": 0,
                            "promos": []
                        }

                    promos_grouped[postback_request.msisdn]["sent_count"] += 1
                    promos_grouped[postback_request.msisdn]["promos"].append({
                        "id": entry.id,
                        "text": entry.text,
                        "created_at": entry.created_at.isoformat()
                    })

                # Foydalanuvchilarni olish
                users_in_month = PostbackRequest.objects.filter(
                    promoentry__created_at__range=(start_date, end_date)
                ).distinct()

                result[month_name] = {
                    "promos": promos_grouped,
                    "users": users_in_month.count()
                }

        return Response(result, status=status.HTTP_200_OK)
    
class PromoEntryList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            # Barcha PostbackRequest yozuvlarini olish
            postback_requests = PostbackRequest.objects.all()
            # Serializer orqali ma'lumotlarni qayta ishlash
            serializer = PostbackRequestSerializerSent(postback_requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PromoCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file_content' not in request.data:
            return Response({"error": "Fayl mazmuni topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        file_content = request.data['file_content']

        try:
            raw_data = file_content.encode('utf-8', errors='replace')
            result = chardet.detect(raw_data)
            encoding = result['encoding']

            file_content = file_content.encode('utf-8').decode(encoding)
            promo_codes = file_content.splitlines()

            # Takroriylarni chiqarib tashlash uchun set ishlatamiz
            promo_codes = list(set([code.strip() for code in promo_codes if code.strip()]))

            batch_size = 10000
            saved_count = 0
            for i in range(0, len(promo_codes), batch_size):
                batch = promo_codes[i:i + batch_size]

                # Bazada borlarini chiqarib tashlaymiz
                existing = set(Promo.objects.filter(promo_text__in=batch).values_list('promo_text', flat=True))
                new_codes = [Promo(promo_text=code) for code in batch if code not in existing]

                Promo.objects.bulk_create(new_codes)
                saved_count += len(new_codes)

            return Response({"message": f"{saved_count} ta yangi promo kod muvaffaqiyatli qo'shildi!"}, status=status.HTTP_201_CREATED)

        except UnicodeDecodeError as e:
            return Response({"error": f"Faylni o‘qishda xatolik: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"Xatolik: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# notification_sent maydonini yangilaydigan funksiya
def reset_notification_sent():
    updated_count = PostbackRequest.objects.filter(notification_sent=True).update(notification_sent=False)
    return updated_count


# GET so'rovni qabul qiladigan view
class ResetNotificationView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # notification_sent maydonini yangilash
        updated_count = reset_notification_sent()

        # Javob qaytarish
        return Response({
            "status": "success",
            "message": f"{updated_count} ta yozuv yangilandi",
        }, status=status.HTTP_200_OK)

@csrf_exempt
def upload_excel_view(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['file']
            try:
                df = pd.read_excel(excel_file)

                current_year = date.today().year
                created = skipped = 0

                for _, row in df.iterrows():
                    raw_date = row.get('Число')
                    # Agar bo'sh bo'lsa skip
                    if pd.isna(raw_date):
                        skipped += 1
                        continue

                    # raw_date Timestamp yoki datetime bo'lishi mumkin
                    if isinstance(raw_date, (pd.Timestamp, )):
                        day = raw_date.day
                        month = raw_date.month
                    else:
                        # Agar faqat raqam bo'lsa, misol uchun "1" bo'lsa, kun deb o'qiymiz va hozirgi oy bilan birlashtiramiz
                        day = int(raw_date)
                        month = date.today().month

                    # Sana obyektини yaratамиз
                    record_date = date(current_year, month, day)

                    prefix = f"Факт дня: {day:02d}-{month:02d} \n"
                    text1 = row.get('Событие1') or ''
                    text2 = row.get('Событие2') or ''
                    text3 = row.get('Событие3') or ''

                    # Бир хил маълумот бор-ёқлигини текшириш
                    exists = NotificationDaily.objects.filter(
                        date=record_date,
                        text1=prefix + text1,
                        text2=prefix + text2,
                        text3=prefix + text3
                    ).exists()
                    if exists:
                        skipped += 1
                        continue

                    # Яратиш
                    NotificationDaily.objects.create(
                        date=record_date,
                        text1=prefix + text1,
                        text2=prefix + text2,
                        text3=prefix + text3,
                    )
                    created += 1

                messages.success(request,
                    f"Import yakunlandi: {created} ta yangi yozuv, {skipped} ta o‘tkazildi.")
                return redirect('upload_excel')

            except Exception as e:
                messages.error(request, f"Xatolik: {e}")
    else:
        form = ExcelUploadForm()

    return render(request, 'upload_excel.html', {'form': form})