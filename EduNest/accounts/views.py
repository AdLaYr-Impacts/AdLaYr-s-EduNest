from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from . import serializers

class RefreshTokenView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer