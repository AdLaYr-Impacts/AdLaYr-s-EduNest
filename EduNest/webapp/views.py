from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from django.db.models import Count, Prefetch, Q
from .models import (
    SchoolTeacher, SchoolClass, Subjects, ExamType, ClassSubjects, SubjectGroup, Students, 
    StudentParentDetails, AttendanceSession, StudentAttendance, Period,
    ClassTimetable, ClassTimetableEntry, Exam, ExamClass,
)
from .serializers import (
    TeacherSerializer, SchoolClassSerializer, TeacherSummarySerializer, 
    SubjectSerializer, ClassListSerializer, SubjectListSerializer,
    ClassSubjectSerializer, ClassSubjectGroupSerializer, SubjectGroupSerializer,
    StudentSerializer, SchoolClassSupportSerializer, StudentSupportSerializer, 
    ClassSubjectSupportSerializer, StudentAttendanceSerializer, PeriodSerializer,
    ClassTimetableSerializer, ExamTypeSerializer, ExamSerializer,
)
from permissions.permissions import IsSchoolAdmin, IsSchoolAdminOrClassTeacher
from common.pagination import StandardPagination
from common.helper import get_school
from common.choices import UserRoles
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers

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
            school=school,
            academic_year=school.academic_year
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
        summary="List all teachers belonging to the school with their subject assignment count for current academic year",
        description="Returns a list of teachers with count of subjects they are assigned to within the school for the current academic year."
    ),
)
class TeacherSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeacherSummarySerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'teacher_code']
    ordering_fields = ['created_at', 'already_assigned_count']
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
            already_assigned_count=Count(
                'subject_teacher',
                filter=Q(
                    subject_teacher__subject_class__school=school,
                    subject_teacher__subject_class__academic_year=school.academic_year,
                    subject_teacher__is_active=True
                ),
                distinct=True
            )
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
            'subject', 'subject_class'
        ).prefetch_related(
            'teacher'
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
            'student_parent_details__user',
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


class StudentSupportView(viewsets.ViewSet):
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination

    @extend_schema(
        tags=['Students'],
        summary="List all classes within school",
        responses={200: SchoolClassSupportSerializer(many=True)}
    )
    def student_classes(self, request, *args, **kwargs):
        school = get_school(self)
        queryset = SchoolClass.objects.filter(school=school, is_active=True).order_by('class_name', 'section')
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = SchoolClassSupportSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SchoolClassSupportSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Students'],
        summary="List all students based on class uuid",
        responses={200: StudentSupportSerializer(many=True)}
    )
    def class_students(self, request, school_id, class_uuid=None, *args, **kwargs):
        school = get_school(self)
        school_class = get_object_or_404(SchoolClass, uuid=class_uuid, school=school)
        
        queryset = Students.objects.filter(
            school=school,
            student_academic_details__student_class=school_class,
            user__is_deleted=False
        ).select_related(
            'user'
        ).prefetch_related(
            'student_academic_details',
            'student_parent_details',
            'student_parent_details__user',
            'student_admission_details'
        ).order_by('user__first_name', 'user__last_name')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = StudentSupportSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = StudentSupportSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['Students'],
        summary="List all subjects based on class uuid",
        responses={200: ClassSubjectSupportSerializer(many=True)}
    )
    def class_subjects(self, request, class_uuid=None, *args, **kwargs):
        school = get_school(self)
        school_class = get_object_or_404(SchoolClass, uuid=class_uuid, school=school)
        
        queryset = ClassSubjects.objects.filter(
            subject_class=school_class,
            subject__school=school,
            is_active=True
        ).select_related('subject').order_by('sort_order', 'subject__name')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = ClassSubjectSupportSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ClassSubjectSupportSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Students Attendance']),
    create=extend_schema(tags=['Students Attendance']),
    retrieve=extend_schema(tags=['Students Attendance']),
    update=extend_schema(tags=['Students Attendance']),
    partial_update=extend_schema(tags=['Students Attendance']),
    destroy=extend_schema(tags=['Students Attendance']),
)
class StudentAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = StudentAttendanceSerializer
    permission_classes = [IsSchoolAdminOrClassTeacher]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session__date', 'status']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__user__username']
    ordering_fields = ['created_at', 'session__date']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if getattr(self, "swagger_fake_view", False):
            return
        
        school = get_school(self)
        class_uuid = self.kwargs.get('class_uuid')

        try:
            class_obj = SchoolClass.objects.get(uuid=class_uuid, school=school)
        except SchoolClass.DoesNotExist:
            raise serializers.ValidationError({"class_uuid": "Class not found in this school."})

        if request.user.role == UserRoles.CLASS_TEACHER:
            teacher = SchoolTeacher.objects.filter(user=request.user, school=school).first()
            if not teacher:
                raise PermissionDenied("Teacher profile not found for this user.")

            is_assigned = (
                class_obj.class_teacher == teacher or
                class_obj.assistant_teacher.filter(id=teacher.id).exists()
            )
            if not is_assigned:
                raise PermissionDenied("You do not have permission to access attendance for this class.")

        self.school = school
        self.class_obj = class_obj

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentAttendance.objects.none()

        return StudentAttendance.objects.filter(
            session__class_obj=self.class_obj
        ).select_related(
            'session',
            'student',
            'student__user'
        ).prefetch_related(
            'student__student_academic_details'
        ).order_by('student__user__first_name', 'student__user__last_name')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            context['school'] = self.school
            context['class_obj'] = self.class_obj
        return context

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Method \"DELETE\" not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@extend_schema_view(
    list=extend_schema(tags=['Periods']),
    create=extend_schema(tags=['Periods']),
    retrieve=extend_schema(tags=['Periods']),
    update=extend_schema(tags=['Periods']),
    partial_update=extend_schema(tags=['Periods']),
    destroy=extend_schema(tags=['Periods']),
)
class PeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PeriodSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_obj__uuid']
    search_fields = ['name']
    ordering_fields = ['created_at', 'start_time', 'end_time', 'order']
    ordering = ['order', 'start_time']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if getattr(self, "swagger_fake_view", False):
            return
        
        class_uuid = self.kwargs.get('class_uuid')
        try:
            school_obj = get_school(self)
            class_obj = SchoolClass.objects.get(uuid=class_uuid, school=school_obj)
        except SchoolClass.DoesNotExist:
            raise serializers.ValidationError({"class_uuid": "Class not found in this school."})
        
        self.school_obj = school_obj
        self.class_obj = class_obj

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Period.objects.none()

        return Period.objects.filter(
            school=self.school_obj,
            class_obj=self.class_obj
        ).select_related('school', 'class_obj').order_by(*self.ordering)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            context['school'] = self.school_obj
            context['class_obj'] = self.class_obj
        return context

    def perform_create(self, serializer):
        serializer.save(
            school=self.school_obj,
            class_obj=self.class_obj
        )

    def perform_update(self, serializer):
        serializer.save()


@extend_schema_view(
    list=extend_schema(tags=['Class Timetable']),
    create=extend_schema(tags=['Class Timetable']),
    retrieve=extend_schema(tags=['Class Timetable']),
    update=extend_schema(tags=['Class Timetable']),
    partial_update=extend_schema(tags=['Class Timetable']),
    destroy=extend_schema(tags=['Class Timetable']),
)
class ClassTimetableViewSet(viewsets.ModelViewSet):
    serializer_class = ClassTimetableSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_obj__uuid', 'class_obj__academic_year', 'is_published', 'is_save_as_draft']
    search_fields = ['class_obj__class_name', 'class_obj__section']
    ordering_fields = ['created_at', 'class_obj__class_name', 'class_obj__academic_year']
    ordering = ['-created_at']

    def get_class_object(self):
        if getattr(self, 'swagger_fake_view', False):
            return None

        school = get_school(self)
        class_uuid = self.kwargs.get('class_uuid')
        if not class_uuid:
            return None

        return get_object_or_404(
            SchoolClass,
            uuid=class_uuid,
            school=school,
            is_active=True,
        )

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ClassTimetable.objects.none()

        school = get_school(self)
        entry_queryset = ClassTimetableEntry.objects.select_related(
            'period',
            'subject',
            'subject__subject',
            'subject__subject_class',
            'teacher',
            'teacher__user',
        ).filter(is_active=True).order_by('day', 'period__order', 'period__start_time')

        return ClassTimetable.objects.filter(
            school=school,
            class_obj=self.get_class_object(),
            class_obj__school=school,
            is_active=True,
        ).select_related(
            'school',
            'class_obj',
            'class_obj__school',
        ).prefetch_related(
            Prefetch('time_table', queryset=entry_queryset)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        if self.action != 'list':
            context['class_obj'] = self.get_class_object()
        return context

    def get_object(self):
        if getattr(self, 'swagger_fake_view', False):
            return None

        school = get_school(self)
        class_obj = self.get_class_object()
        timetable_uuid = self.kwargs.get('uuid')
        obj = self.get_queryset().filter(
            school=school,
            class_obj=class_obj,
            uuid=timetable_uuid,
        ).first()

        if not obj:
            raise Http404

        return obj

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    # def perform_destroy(self, instance):
    #     instance.is_active = False
    #     instance.save(update_fields=['is_active', 'updated_at'])
    #     instance.time_table.update(is_active=False)


@extend_schema_view(
    list=extend_schema(tags=['Exam Types']),
    create=extend_schema(tags=['Exam Types']),
    retrieve=extend_schema(tags=['Exam Types']),
    update=extend_schema(tags=['Exam Types']),
    partial_update=extend_schema(tags=['Exam Types']),
    destroy=extend_schema(tags=['Exam Types']),
)
class ExamTypeViewSet(viewsets.ModelViewSet):
    serializer_class = ExamTypeSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']
    ordering_fields = ['created_at', 'name']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ExamType.objects.none()
        school = get_school(self)
        return ExamType.objects.filter(
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
    list=extend_schema(tags=['Exams']),
    create=extend_schema(tags=['Exams']),
    retrieve=extend_schema(tags=['Exams']),
    update=extend_schema(tags=['Exams']),
    partial_update=extend_schema(tags=['Exams']),
    destroy=extend_schema(tags=['Exams']),
)
class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [IsSchoolAdmin]
    pagination_class = StandardPagination
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'status', 'is_locked', 'exam_type__uuid']
    search_fields = ['name', 'exam_type__name', 'exam_classes__class_obj__class_name', 'exam_classes__class_obj__section']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'name', 'academic_year', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Exam.objects.none()

        school = get_school(self)
        exam_class_queryset = ExamClass.objects.select_related(
            'class_obj',
            'class_obj__school',
        ).order_by('class_obj__class_name', 'class_obj__section')

        queryset = Exam.objects.filter(
            school=school,
            is_active=True,
        ).select_related(
            'school',
            'exam_type',
            'created_by',
        ).prefetch_related(
            Prefetch('exam_classes', queryset=exam_class_queryset)
        ).distinct()

        if self.action == 'list':
            academic_year = self.request.query_params.get('academic_year', school.academic_year)
            if academic_year:
                queryset = queryset.filter(academic_year=academic_year)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['school'] = get_school(self)
        return context

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"is_locked": "This exam is locked and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.localdate() >= instance.start_date:
            return Response(
                {"start_date": "This exam has already started and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)
