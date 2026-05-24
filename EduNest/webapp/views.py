from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Count
from .models import SchoolTeacher, SchoolClass
from .serializers import TeacherSerializer, SchoolClassSerializer, TeacherSummarySerializer
from permissions.permissions import IsSchoolAdmin
from common.pagination import StandardPagination
from common.helper import get_school

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

    def get_queryset(self):
        school = get_school(self)
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
            context['school'] = get_school(self)
        return context

    def update(self, request, *args, **kwargs):
        """
        Allow partial updates for PUT requests to support resetting credentials.
        """
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        user = instance.user
        user.is_deleted = True
        user.is_active = False
        user.save()
        
        instance.is_active = False
        instance.save()


@extend_schema_view(
    list=extend_schema(tags=['Classes']),
    create=extend_schema(tags=['Classes']),
    retrieve=extend_schema(tags=['Classes']),
    update=extend_schema(tags=['Classes']),
    partial_update=extend_schema(tags=['Classes']),
    destroy=extend_schema(tags=['Classes']),
)
class SchoolClassViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolClassSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'medium', 'board', 'smart_class_enabled']
    search_fields = ['class_name', 'section', 'classroom_number']
    ordering_fields = ['created_at', 'class_name', 'academic_year']

    def get_queryset(self):
        school = get_school(self)
        return SchoolClass.objects.filter(
            school=school
        ).select_related(
            'class_teacher', 'class_teacher__user', 'school'
        ).prefetch_related(
            'assistant_teacher', 'assistant_teacher__user'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context


@extend_schema_view(
    list=extend_schema(
        tags=['Teachers'],
        summary="List all teachers belonging to the school with their class assignments",
        description="Returns a list of teachers with counts of classes where they are class teachers or assistant teachers."
    ),
)
class TeacherSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeacherSummarySerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'teacher_code']
    ordering_fields = ['created_at', 'class_teacher_count', 'assistant_class_teacher_count']
    ordering = ['-created_at']

    def get_queryset(self):
        school = get_school(self)
        return SchoolTeacher.objects.filter(
            school=school,
            user__is_deleted=False
        ).select_related(
            'user'
        ).annotate(
            class_teacher_count=Count('classes_as_class_teacher', distinct=True),
            assistant_class_teacher_count=Count('classes_as_assistant_teacher', distinct=True)
        )

