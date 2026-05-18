from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from .models import SchoolTeacher, School
from .serializers import TeacherSerializer
from permissions.permissions import IsSchoolAdmin
from common.pagination import StandardPagination

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=['Teachers']),
    create=extend_schema(tags=['Teachers']),
    retrieve=extend_schema(tags=['Teachers']),
    update=extend_schema(tags=['Teachers']),
    partial_update=extend_schema(tags=['Teachers']),
    destroy=extend_schema(tags=['Teachers']),
)
class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'employment_type']
    search_fields = ['user__first_name', 'user__last_name', 'teacher_code', 'user__email', 'user__phone_number']
    ordering_fields = ['created_at', 'joining_date']

    def get_school(self):
        school_uuid = self.kwargs.get('school_id')
        school = get_object_or_404(School, uuid=school_uuid)
        
        if self.request.user.school != school:
            raise PermissionDenied("You do not have permission to access this school's data.")
        
        return school

    def get_queryset(self):
        school = self.get_school()
        return SchoolTeacher.objects.filter(
            school=school,
            user__is_deleted=False
        ).select_related(
            'user', 'school'
        ).prefetch_related(
            'teacher_education', 
            'teacher_experiance', 
            'teacher_employment'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == 'create':
            context['school'] = self.get_school()
        return context

    def perform_destroy(self, instance):
        user = instance.user
        user.is_deleted = True
        user.is_active = False
        user.save()
        
        instance.is_active = False
        instance.save()
