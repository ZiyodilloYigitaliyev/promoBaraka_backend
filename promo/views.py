import requests
import chardet
from rest_framework.parsers import FileUploadParser
import json
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
            return Response({'message': custom_message}, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            return Response({"error": "Failed to send SMS", "details": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    def get(self, request, *args, **kwargs):
        msisdn = request.query_params.get('msisdn')
        opi = request.query_params.get('opi')
        short_number = request.query_params.get('short_number')
        text = request.query_params.get('message')

        custom_message = ""

        if msisdn and opi and short_number and text:
            promo = Promo.objects.filter(promo_text=text).first()
            if promo is None:
                custom_message = "Jo’natilgan Promokod noto’g’ri!"
                return self.send_sms(msisdn, opi, short_number, custom_message)

            # Filterlashda postback_request orqali msisdn ga murojaat qiling
            if PromoEntry.objects.filter(postback_request__msisdn=msisdn, text=text).exists():
                custom_message = "Quyidagi Promokod avval ro’yxatdan o’tkazilgan!"
                return self.send_sms(msisdn, opi, short_number, custom_message)

            postback_request = PostbackRequest.objects.filter(msisdn=msisdn).first()
            if postback_request:
                postback_request.sent_count += 1
                postback_request.save()
                PromoEntry.objects.create(
                    postback_request=postback_request, 
                    text=text,
                    created_at=timezone.now()
                )
            else:
                postback_request = PostbackRequest.objects.create(
                    msisdn=msisdn,
                    opi=opi,
                    short_number=short_number,
                    sent_count=1
                )
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

            # # Qo'shimcha notification xabari yuborish uchun
            # if response.status_code == 200:
            #     self.notification_sms(msisdn, opi, short_number)

            return response
        else:
            return Response({"error": "Failed to send SMS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    # def notification_sms(self, msisdn, opi, short_number):
    #     today = timezone.now().date()
    #     notification = Notification.objects.filter(date=today).first()

    #     # Qo'shimcha SMS faqat bir marta yuboriladi va faqat opi=23 uchun
    #     if int(opi) == 27 and notification:
    #         if not PostbackRequest.objects.filter(msisdn=msisdn, notification_sent=True).exists():
    #             notification_message = notification.text
    #             sms_api_url = "https://cp.vaspool.com/api/v1/sms/send?token=sUt1TCRZdhKTWXFLdOuy39JByFlx2"
    #             params = {
    #                 'opi': opi,
    #                 'msisdn': msisdn,
    #                 'short_number': short_number,
    #                 'message': notification_message
    #             }
    #             try:
    #                 requests.get(sms_api_url, params=params)
    #                 # SMS yuborilgandan so'ng flagni o'rnatish
    #                 PostbackRequest.objects.filter(msisdn=msisdn).update(notification_sent=True)
    #             except requests.RequestException as e:
    #                 print("Failed to send notification SMS:", e)


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
        # JSON ma'lumotni tekshirish
        if 'file_content' not in request.data:
            return Response({"error": "Fayl mazmuni topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        file_content = request.data['file_content']

        try:
            # Fayl kodlash turini aniqlash
            raw_data = file_content.encode('utf-8', errors='replace')
            result = chardet.detect(raw_data)
            encoding = result['encoding']

            # Fayl mazmunini aniqlangan kodlash turi bilan to'liq o'qish
            file_content = file_content.encode('utf-8').decode(encoding)
            promo_codes = file_content.splitlines()

            # Promo kodlarni Promo modeliga saqlash
            batch_size = 10000  # Har safar 10,000 ta kodni saqlash
            for i in range(0, len(promo_codes), batch_size):
                batch = promo_codes[i:i + batch_size]
                promo_objects = [Promo(promo_text=code.strip()) for code in batch if code.strip()]
                Promo.objects.bulk_create(promo_objects)  # Har 10,000 ta promo kodni bazaga saqlash

            return Response({"message": "Promo kodlar muvaffaqiyatli bazaga qo'shildi!"},
                            status=status.HTTP_201_CREATED)

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

