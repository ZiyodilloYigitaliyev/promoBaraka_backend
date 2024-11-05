from django.urls import path
from .views import *
from promo.main import app as fastapi_app
from fastapi.middleware.wsgi import WSGIMiddleware




urlpatterns = [
    path('postback-callback/', PostbackCallbackView.as_view()),
    path('promo-entries/monthly/', PromoMonthlyView.as_view()),
    path('promo/', PromoEntryList.as_view()),
    path('Promo-add/', PromoCreateView.as_view()),
    path("api/postback/", WSGIMiddleware(fastapi_app)),

]
