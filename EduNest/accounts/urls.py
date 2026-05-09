from django.urls import path
from rest_framework_simplejwt.views import(
    TokenRefreshView
)
from . views import RefreshTokenView, SchoolAdminViewSet

urlpatterns = [
    path('token/', RefreshTokenView.as_view()), # Get Token with customized response
    path('token/refresh/', TokenRefreshView.as_view()),
    
    path('schools/<uuid:school_id>/admins/', SchoolAdminViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('schools/<uuid:school_id>/admins/<uuid:id>/', SchoolAdminViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]
