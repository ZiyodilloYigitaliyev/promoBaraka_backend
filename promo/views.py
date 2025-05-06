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
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import timedelta, datetime
from rest_framework.viewsets import ViewSet
from .serializers import *
from rest_framework.parsers import MultiPartParser
from .tasks import process_promo_file


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
            sms_response = requests.get(sms_api_url, params=params)
            sms_response.raise_for_status()
            return sms_response
        except requests.RequestException as e:
            return None

    def get(self, request, *args, **kwargs):
        msisdn = request.query_params.get('msisdn')
        opi = request.query_params.get('opi')
        short_number = request.query_params.get('short_number')
        text = request.query_params.get('message')

        if short_number == "7500":
            if msisdn and opi and text:
                promo = Promo.objects.filter(promo_text=text).first()
                if not promo:
                    custom_message = "Jo’natilgan Promokod noto’g’ri!"
                    response = self.send_sms(msisdn, opi, short_number, custom_message)
                    return Response({"message": custom_message}, status=status.HTTP_200_OK)

                if PromoEntry.objects.filter(postback_request__msisdn=msisdn, text=text).exists():
                    custom_message = "Quyidagi Promokod avval ro’yxatdan o’tkazilgan!"
                    response = self.send_sms(msisdn, opi, short_number, custom_message)
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

                custom_message = (
                    "Tabriklaymiz! Promokod qabul qilindi!\n"
                    "\"Boriga baraka\" ko'rsatuvini har Juma soat 21:00 da Jonli efirda tomosha qiling!"
                )
                response = self.send_sms(msisdn, opi, short_number, custom_message)
                if response:
                    return Response({"message": custom_message}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Failed to send SMS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "7500 uchun kerakli parametrlar yetarli emas!"}, status=status.HTTP_400_BAD_REQUEST)

        elif short_number == "07500":
            reqid = request.query_params.get('reqid')
            result = request.query_params.get('result')

            if msisdn and opi and reqid and result:
                try:
                    QueryLog.objects.create(
                        msisdn=msisdn,
                        opi=opi,
                        short_number=short_number,
                        reqid=reqid,
                        result=result
                    )

                    message_1 = "Sizning arizangiz qabul qilindi, javob SMSni kuting."
                    message_2 = (
                        "Boriga Baraka Kapital Shou uchun kodingiz qabul qilindi. "
                        "Efir Zo'r TV kanalida har juma soat 20.20 da. "
                        "Spasibo! Kod prinyat. Sledite za efirom na Zo'r TV kanale kajduyu pyatnitsu v 20.20. "
                        "Tel: 998(78)147-78-89."
                    )

                    response_1 = self.send_sms(msisdn, opi, short_number, message_1)
                    response_2 = self.send_sms(msisdn, opi, short_number, message_2)

                    
                    try:
                        # Server vaqti (odatda UTC) ni olish
                        server_now = timezone.now()

                        # Tashkent vaqti uchun timezone aniqlash
                        tashkent_tz = pytz.timezone("Asia/Tashkent")
                        tashkent_now = server_now.astimezone(tashkent_tz)
                        today = tashkent_now.date()  # Bugungi sana, Tashkent vaqtiga mos

                        # Bugungi sana uchun NotificationDaily yozuvini olish
                        notification = NotificationDaily.objects.filter(date=today).first()
                        if not notification:
                            return Response({"error": "Bugungi Notification topilmadi!"}, status=404)

                        # text1, text2, text3 maydonlaridan bo'sh bo'lmaganlarini tanlab olish
                        possible_texts = [text for text in [notification.text1, notification.text2, notification.text3] if text]
                        if not possible_texts:
                            return Response({"error": "Notification matni topilmadi!"}, status=404)

                        # Tasodifiy matn tanlash
                        notification_message = random.choice(possible_texts)

                        # SMS yuborish funksiyasi yordamida yuborish
                        notification_response = self.send_sms(msisdn, opi, short_number, notification_message)

                    except Exception as e:
                        return Response({"error": str(e)}, status=500)
                    if response_1 and response_2 and notification_response:
                        return Response({"message": "Barcha SMS muvaffaqiyatli yuborildi!"}, status=status.HTTP_200_OK)
                    else:
                        errors = []
                        if not response_1:
                            errors.append("SMS 1 yuborilmadi!")
                        if not response_2:
                            errors.append("SMS 2 yuborilmadi!")
                        if not notification_response:
                            errors.append("Notification SMS yuborilmadi!")
                        return Response({"error": "SMS yuborishda xatolik yuz berdi!", "details": errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                except Exception as e:
                    return Response({"error": "Bazaga saqlashda yoki SMS yuborishda xatolik yuz berdi!", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                missing_params = []
                if not msisdn:
                    missing_params.append('msisdn')
                if not opi:
                    missing_params.append('opi')
                if not reqid:
                    missing_params.append('reqid')
                if not result:
                    missing_params.append('result')

                return Response({"error": "07500 uchun kerakli parametrlar yetarli emas!", "missing_params": missing_params}, status=status.HTTP_400_BAD_REQUEST)




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
    parser_classes = [MultiPartParser]  # Faylni stream orqali qabul qilish

    def post(self, request):
        """
        Katta hajmdagi faylni qabul qilib, fon rejimida Celery vazifasiga topshiradi.
        Har 10,000 ta kodni alohida batch sifatida yuboradi.
        """
        # Faylni olish
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {"error": "Fayl topilmadi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fayl kengaytmasini tekshirish
        if not file_obj.name.endswith('.txt'):
            return Response(
                {"error": "Faqat .txt kengaytmali fayllar qabul qilinadi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Faylni qatorma-qator generator bilan o‘qish
        def line_generator(f):
            for raw in f:
                try:
                    text = raw.decode('utf-8').strip()
                except UnicodeDecodeError:
                    try:
                        text = raw.decode('latin-1').strip()
                    except UnicodeDecodeError as e:
                        print(f"Xatolik: {e}")
                        continue
                yield text

        # Faylni batchlarga bo'lish va Celery vazifasiga yuborish
        batch_size = getattr(settings, "PROMO_BATCH_SIZE", 10000)
        batch = []

        for line in line_generator(file_obj):
            if line:
                batch.append(line)
            if len(batch) >= batch_size:
                try:
                    import_promos.delay(batch)
                except Exception as e:
                    return Response(
                        {"error": f"Batchni Celeryga yuborishda xatolik yuz berdi: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                batch = []

        # Oxirgi qoldiq batch
        if batch:
            try:
                import_promos.delay(batch)
            except Exception as e:
                return Response(
                    {"error": f"Batchni Celeryga yuborishda xatolik yuz berdi: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"message": "Import vazifasi fon rejimida boshlandi."},
            status=status.HTTP_202_ACCEPTED
        )


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

