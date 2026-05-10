from django.urls import path
from . import views

urlpatterns = [
    path('schools/', views.SchoolViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='school-list'),
    path('schools/<uuid:uuid>/', views.SchoolViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='school-detail'),
]
