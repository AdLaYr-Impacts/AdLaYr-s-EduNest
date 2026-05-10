from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from . import serializers
from .models import Users
from webapp.models import School
from common.choices import UserRoles
from permissions.permissions import IsSuperAdmin

class RefreshTokenView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer

class SchoolAdminViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SchoolAdminSerializer
    permission_classes = [IsSuperAdmin]
    lookup_field = 'uuid'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        school_id = self.kwargs.get('school_id')
        get_object_or_404(School, uuid=school_id)
        return Users.objects.filter(
            school__uuid=school_id, 
            role=UserRoles.SCHOOL_ADMIN,
            is_deleted=False
        ).select_related('school')

    def perform_create(self, serializer):
        school_id = self.kwargs.get('school_id')
        school = get_object_or_404(School, uuid=school_id)
        serializer.save(
            school=school,
            role=UserRoles.SCHOOL_ADMIN
        )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.save()