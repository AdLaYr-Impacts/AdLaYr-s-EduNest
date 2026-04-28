from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('edunest/dev-admin/logup/', admin.site.urls),
    path('edunest/api/', include("permissions.urls")),
    path('edunest/api/', include("accounts.urls")),
    path('edunest/api/', include("webapp.urls")),
    path('edunest/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('edunest/api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('edunest/api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
