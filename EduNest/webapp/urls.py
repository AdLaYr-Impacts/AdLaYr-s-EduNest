from django.urls import path
from . import views

urlpatterns = [
    path("school_admin/", views.SchoolAdminView.as_view()),
    path("class_teacher/", views.ClassTeacherView.as_view()),
]
