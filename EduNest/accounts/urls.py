from django.urls import path
from rest_framework_simplejwt.views import(
    TokenRefreshView
)
from . views import RefreshTokenView

urlpatterns = [
    path('token/', RefreshTokenView.as_view()), # Get Token with customized response
    path('token/refresh/', TokenRefreshView.as_view()),
]
