from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from . import serializers
from .models import Users
from webapp.models import School
from common.choices import UserRoles
from common.helper import generate_user_code
from permissions.permissions import IsSuperAdmin

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema(tags=['Authentication'])
class RefreshTokenView(TokenObtainPairView):
    serializer_class = serializers.CustomTokenObtainPairSerializer

@extend_schema_view(
    list=extend_schema(tags=['School Admins']),
    create=extend_schema(tags=['School Admins']),
    retrieve=extend_schema(tags=['School Admins']),
    update=extend_schema(tags=['School Admins']),
    partial_update=extend_schema(tags=['School Admins']),
    destroy=extend_schema(tags=['School Admins']),
)
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
        user_code = generate_user_code(school, UserRoles.SCHOOL_ADMIN)
        serializer.save(
            school=school,
            role=UserRoles.SCHOOL_ADMIN,
            username=user_code
        )

    def perform_update(self, serializer):
        # To ensure username (user code) is not updated if passed in request data
        serializer.save(username=serializer.instance.username)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.is_active = False
        instance.save()