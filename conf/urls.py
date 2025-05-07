
from django.contrib import admin
from django.template.context_processors import static
from django.urls import path, include
from conf import settings
from promo.views import upload_excel_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('adminBaraka/admin', admin.site.urls),
    path('adminBaraka-next/admin-file/upload-excel/', upload_excel_view, name='upload_excel'),
    path('api/', include('promo.urls')),
    path('api/', include('auth_admin.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
