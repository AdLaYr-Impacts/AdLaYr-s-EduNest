from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'schools', views.SchoolViewSet, basename='school')

urlpatterns = [
    path('', include(router.urls)),
]
