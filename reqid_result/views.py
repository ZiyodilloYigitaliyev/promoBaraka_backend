from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SMSRequest
from .serializers import SMSRequestSerializer
from rest_framework.permissions import AllowAny
import requests

class SMSHandlerView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Query parametrlarni olish
            msisdn = request.query_params.get("msisdn")
            opi = request.query_params.get("opi")
            short_number = request.query_params.get("short_number")

            # Parametrlarni tekshirish
            if not all([msisdn, opi, short_number]):
                return Response(
                    {"error": "Missing required query parameters (msisdn, opi, short_number)"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # SMS yuborish
            self.send_sms(
                msisdn,
                opi,
                short_number,
                "Sizning arizangiz qabul qilindi, javob SMSni kuting"
            )
            self.send_sms(
                msisdn,
                opi,
                short_number,
                (
                    "Boriga Baraka Kapital Shou uchun kodingiz qabul qilindi. Efir Zo'r TV kanalida har juma soat 20.20 da. "
                    "Spasibo! Kod prinyat. Sledite za efirom na Zo'r TV kanale kajduyu pyatnitsu v 20.20 Tel: 998(78)147-78-89."
                )
            )
            self.send_sms(
                msisdn,
                opi,
                short_number,
                "Факт дня"
            )

            return Response({"success": "SMS yuborildi"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def send_sms(self, msisdn, opi, short_number, custom_message):
        """SMS yuborish uchun yordamchi funksiya."""
        sms_api_url = "https://cp.vaspool.com/api/v1/sms/send?token=sUt1TCRZdhKTWXFLdOuy39JByFlx2"
        params = {
            'opi': opi,
            'msisdn': msisdn,
            'short_number': short_number,
            'message': custom_message
        }
        try:
            sms_response = requests.get(sms_api_url, params=params)
            sms_response.raise_for_status()  # Agar xatolik bo‘lsa, ularni ko‘rsatadi
            return {"success": True, "message": custom_message}
        except requests.RequestException as e:
            print(f"Failed to send SMS to {msisdn}: {str(e)}")
            return {"success": False, "error": str(e)}
