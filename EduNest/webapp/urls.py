from django.urls import path
from .views import (
    TeacherViewSet, SchoolClassViewSet, TeacherSummaryViewSet, 
    SubjectViewSet, SubjectListViews, ClassSubjectViewSet, SubjectGroupViewSet
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
]
