from django.urls import path
from .views import SMSHandlerView

urlpatterns = [
    path('sms-handler/', SMSHandlerView.as_view(), name='sms-handler'),
]
