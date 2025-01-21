from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SMSRequest
from .serializers import SMSRequestSerializer
import requests

class SMSHandlerView(APIView):
    def post(self, request):
        try:
            # Сериалайзердан фойдаланиб маълумотларни текшириш
            serializer = SMSRequestSerializer(data=request.data)
            if serializer.is_valid():
                sms_request = serializer.save()

                # SMS юбориш
                self.send_sms(sms_request.msisdn, "Sizning arizangiz qabul qilindi, javob SMSni kuting")
                self.send_sms(
                    sms_request.msisdn,
                    "Boriga Baraka Kapital Shou uchun kodingiz qabul qilindi. Efir Zo'r TV kanalida har juma soat 20.20 da. Spasibo! Kod prinyat. Sledite za efirom na Zo'r TV kanale kajduyu pyatnitsu v 20.20 Tel: 998(78)147-78-89."
                )
                self.send_sms(sms_request.msisdn, "Факт дня")

                return Response({"success": "Ma'lumotlar bazaga saqlandi va SMS yuborildi"}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

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
            return {"success": True, "message": custom_message}
        except requests.RequestException as e:
            print(f"Failed to send SMS to {msisdn}: {str(e)}")
        return {"success": False, "error": str(e)}

