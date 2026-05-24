from django.urls import path
from .views import TeacherViewSet, SchoolClassViewSet, TeacherSummaryViewSet

urlpatterns = [
    path('teachers/', TeacherViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('teachers/list/', TeacherSummaryViewSet.as_view({
        'get': 'list'
    })),
    path('teachers/<uuid:uuid>/', TeacherViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('classes/', SchoolClassViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('classes/<uuid:uuid>/', SchoolClassViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]
