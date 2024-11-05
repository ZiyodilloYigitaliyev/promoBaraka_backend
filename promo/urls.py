from django.urls import path
from .views import *





urlpatterns = [
    path('postback-callback/', PostbackCallbackView.as_view()),
    path('promo-entries/monthly/', PromoMonthlyView.as_view()),
    path('promo/', PromoEntryList.as_view()),
    path('Promo-add/', PromoCreateView.as_view()),

]
