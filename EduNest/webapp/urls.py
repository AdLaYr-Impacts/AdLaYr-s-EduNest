from django.urls import path
from .views import (
    TeacherViewSet, SchoolClassViewSet, TeacherSummaryViewSet, 
    SubjectViewSet, SubjectListViews, ClassSubjectViewSet, SubjectGroupViewSet,
    StudentViewSet, StudentSupportView, StudentAttendanceViewSet, PeriodViewSet,
    ClassTimetableViewSet,
)

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
    path('subjects/', SubjectViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('subjects/<uuid:uuid>/', SubjectViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('subject-list/classes/', SubjectListViews.as_view({
        'get': 'classes'
    })),
    path('subject-list/subjects/', SubjectListViews.as_view({
        'get': 'subjects'
    })),
    path('class-subjects/', ClassSubjectViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('class-subjects/<uuid:uuid>/', ClassSubjectViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('subject-groups/', SubjectGroupViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('subject-groups/<uuid:uuid>/', SubjectGroupViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('students/', StudentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('students/<uuid:uuid>/', StudentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('students/<uuid:uuid>/delete-credential/', StudentViewSet.as_view({
        'delete': 'delete_parent_credential'
    })),
    path('students/classes/', StudentSupportView.as_view({
        'get': 'student_classes'
    })),
    path('students/class/<uuid:class_uuid>/', StudentSupportView.as_view({
        'get': 'class_students'
    })),
    path('students/class/<uuid:class_uuid>/subjects/', StudentSupportView.as_view({
        'get': 'class_subjects'
    })),
    path('student_attendance/<uuid:class_uuid>/', StudentAttendanceViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('student_attendance/<uuid:class_uuid>/<uuid:uuid>/', StudentAttendanceViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update'
    })),
    path('classes/<uuid:class_uuid>/periods/', PeriodViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('classes/<uuid:class_uuid>/periods/<uuid:uuid>/', PeriodViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('classes/<uuid:class_uuid>/class_timetable/', ClassTimetableViewSet.as_view({
        'get': 'list',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update'
    })),
    path('classes/<uuid:class_uuid>/class_timetable/<uuid:uuid>/', ClassTimetableViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]
