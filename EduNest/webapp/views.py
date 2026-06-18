from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Count, Prefetch
from .models import SchoolTeacher, SchoolClass, Subjects, ClassSubjects, SubjectGroup, Students, StudentParentDetails
from .serializers import (
    TeacherSerializer, SchoolClassSerializer, TeacherSummarySerializer, 
    SubjectSerializer, ClassListSerializer, SubjectListSerializer,
    ClassSubjectSerializer, ClassSubjectGroupSerializer, SubjectGroupSerializer,
    StudentSerializer
)
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
        if getattr(self, "swagger_fake_view", False):
            return SchoolTeacher.objects.none()
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
        if getattr(self, "swagger_fake_view", False):
            return SchoolClass.objects.none()
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
        summary="List all teachers belonging to the school with their class assignment count",
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
        if getattr(self, "swagger_fake_view", False):
            return SchoolTeacher.objects.none()
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


@extend_schema_view(
    list=extend_schema(tags=['Subjects']),
    create=extend_schema(tags=['Subjects']),
    retrieve=extend_schema(tags=['Subjects']),
    update=extend_schema(tags=['Subjects']),
    partial_update=extend_schema(tags=['Subjects']),
    destroy=extend_schema(tags=['Subjects']),
)
class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject_type', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name', 'code']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Subjects.objects.none()
        school = get_school(self)
        return Subjects.objects.filter(
            school=school
        ).select_related('school')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema_view(
    classes=extend_schema(
        tags=['Subjects'],
        summary="Subject lists to assign classes",
        responses={200: SubjectListSerializer(many=True)}
    ),
    subjects=extend_schema(
        tags=['Subjects'],
        summary="Grouped Class and Subject list",
        responses={200: ClassSubjectGroupSerializer(many=True)}
    )
)
class SubjectListViews(viewsets.ViewSet):
    pagination_class = StandardPagination
    permission_classes = [IsSchoolAdmin]

    @action(detail=False, methods=['get'])
    def subjects(self, request, *args, **kwargs):
        school = get_school(self)
        queryset = Subjects.objects.filter(
            school=school, 
            is_active=True
        ).only('uuid', 'code', 'name')

        class_uuid = request.query_params.get('class')
        if class_uuid:
            if not SchoolClass.objects.filter(uuid=class_uuid, school=school).exists():
                return Response(
                    {"detail": "Class not found or does not belong to your school."},
                    status=status.HTTP_404_NOT_FOUND
                )
            queryset = queryset.exclude(
                class_subjects__subject_class__uuid=class_uuid,
                class_subjects__subject_class__school=school,
                class_subjects__is_active=True
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = SubjectListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SubjectListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def classes(self, request, *args, **kwargs):
        school = get_school(self)
        queryset = SchoolClass.objects.filter(
            school=school, 
            is_active=True
        ).prefetch_related(
            Prefetch(
                'class_as_subject_class',
                queryset=ClassSubjects.objects.filter(
                    is_active=True, 
                    subject__is_active=True
                ).select_related('subject'),
                to_attr='active_subjects'
            )
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ClassSubjectGroupSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ClassSubjectGroupSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Class Subjects']),
    create=extend_schema(tags=['Class Subjects']),
    retrieve=extend_schema(tags=['Class Subjects']),
    update=extend_schema(tags=['Class Subjects']),
    partial_update=extend_schema(tags=['Class Subjects']),
    destroy=extend_schema(tags=['Class Subjects']),
)
class ClassSubjectViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSubjectSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject_class__uuid', 'subject__uuid', 'teacher__uuid', 'is_optional', 'is_language']
    search_fields = ['subject__name', 'subject__code', 'subject_class__class_name', 'teacher__user__first_name', 'teacher__user__last_name']
    ordering_fields = ['created_at', 'sort_order', 'max_marks', 'pass_marks']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ClassSubjects.objects.none()
        school = get_school(self)
        return ClassSubjects.objects.filter(
            subject_class__school=school
        ).select_related(
            'subject', 'subject_class', 'teacher', 'teacher__user'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=['Subject Groups']),
    create=extend_schema(tags=['Subject Groups']),
    retrieve=extend_schema(tags=['Subject Groups']),
    update=extend_schema(tags=['Subject Groups']),
    partial_update=extend_schema(tags=['Subject Groups']),
    destroy=extend_schema(tags=['Subject Groups']),
)
class SubjectGroupViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectGroupSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'name', 'code']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SubjectGroup.objects.none()
        school = get_school(self)
        return SubjectGroup.objects.filter(
            school=school
        ).select_related(
            'school'
        ).prefetch_related(
            'classes'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=['Students']),
    create=extend_schema(tags=['Students']),
    retrieve=extend_schema(tags=['Students']),
    update=extend_schema(tags=['Students']),
    partial_update=extend_schema(tags=['Students']),
    destroy=extend_schema(tags=['Students']),
    delete_parent_credential=extend_schema(
        tags=['Students'],
        summary="Delete student parent credential",
        description="Deletes the login credentials of the student's parent.",
    ),
)
class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student_admission_details__student_status', 'student_academic_details__student_class__uuid']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__username', 
        'user__email', 'user__phone_number', 
        'student_admission_details__admission_number'
    ]
    ordering_fields = ['created_at', 'user__first_name']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Students.objects.none()
        school = get_school(self)
        return Students.objects.filter(
            school=school,
            user__is_deleted=False
        ).select_related(
            'user', 'school'
        ).prefetch_related(
            'student_admission_details',
            'student_parent_details',
            'student_academic_details',
            'student_academic_details__student_class',
            'student_academic_details__subject_group'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        user = instance.user
        user.is_deleted = True
        user.is_active = False
        user.save()
        
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['delete'], url_path='delete-credential')
    def delete_parent_credential(self, request, uuid=None, **kwargs):
        instance = get_object_or_404(self.get_queryset(), uuid=uuid)

        parent_detail = instance.student_parent_details.filter(user__isnull=False).first()
        if not parent_detail:
            return Response(
                {"detail": "No parent user linked to this student."},
                status=status.HTTP_400_BAD_REQUEST
            )

        parent_user = parent_detail.user

        with transaction.atomic():
            parent_detail.user = None
            parent_detail.save(update_fields=['user'])

            if not StudentParentDetails.objects.filter(user=parent_user).exists():
                parent_user.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)