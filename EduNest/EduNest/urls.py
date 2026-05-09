from django.urls import path, include
from webapp.admin import admin_site
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('edunest/dev-admin/access/', admin_site.urls),
    path('edunest/api/', include("permissions.urls")),
    path('edunest/api/accounts/', include("accounts.urls")),
    path('edunest/api/', include("webapp.urls")),
    path('edunest/api/s_admin/', include("s_admin.urls")),
    path('edunest/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('edunest/api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('edunest/api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
