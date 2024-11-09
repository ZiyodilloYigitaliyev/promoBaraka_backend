from django.urls import path
from .views import *





urlpatterns = [
    path('postback-callback/', PostbackCallbackView.as_view()),
    path('promo-entries/monthly/', PromoMonthlyView.as_view()),
    path('promo/', PromoEntryList.as_view()),
    path('Promo-add/', PromoCreateView.as_view()),
     path("fetch-data/", FetchAndSaveDataView.as_view(), name="fetch_data")
    path('reset-notification/', ResetNotificationView.as_view(), name='daily-request'),

]
