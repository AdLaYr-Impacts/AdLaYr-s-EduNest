from django.contrib import admin
from ..models import (
    SchoolClass, Subjects, ClassSubjects, SubjectGroup, AttendanceSession, 
    ClassTimetable, ClassTimetableEntry, ExamClass, ExamSchedule, EventClass
)
from . import admin_site

@admin.register(SchoolClass, site=admin_site)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_name', 'section', 'school', 'academic_year', 'medium', 'is_active')
    list_filter = ('school', 'academic_year', 'medium', 'is_active')
    search_fields = ('class_name', 'section', 'school__short_name')

@admin.register(Subjects, site=admin_site)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'school', 'subject_type', 'is_active')
    list_filter = ('school', 'subject_type', 'is_active')
    search_fields = ('name', 'code', 'school__short_name')

@admin.register(ClassSubjects, site=admin_site)
class ClassSubjectsAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'subject_class', 'max_marks', 'pass_marks', 'is_active')
    list_filter = ('subject_class__school', 'subject_class', 'is_active')
    search_fields = ('subject__name', 'subject_class__class_name', 'teacher__user__first_name')

@admin.register(SubjectGroup, site=admin_site)
class SubjectGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'school', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('name', 'code', 'school__short_name')

@admin.register(AttendanceSession, site=admin_site)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_obj', 'date', 'total_students', 'present_count', 'absent_count', 'is_active')
    list_filter = ('class_obj__school', 'class_obj', 'date')
    search_fields = ('class_obj__class_name', 'date')

@admin.register(ClassTimetable, site=admin_site)
class ClassTimetableAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'class_obj', 'is_published', 'is_save_as_draft', 'is_active')
    list_filter = ('school', 'class_obj', 'is_published', 'is_active')
    search_fields = ('class_obj__class_name', 'school__short_name')

@admin.register(ClassTimetableEntry, site=admin_site)
class ClassTimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'timetable', 'day', 'period', 'subject', 'teacher', 'is_active')
    list_filter = ('timetable__class_obj__school', 'day', 'is_active')
    search_fields = ('timetable__class_obj__class_name', 'subject__subject__name', 'teacher__user__first_name')

@admin.register(ExamClass, site=admin_site)
class ExamClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'class_obj', 'is_active')
    list_filter = ('exam__school', 'class_obj', 'is_active')
    search_fields = ('exam__name', 'class_obj__class_name')

@admin.register(ExamSchedule, site=admin_site)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam_class', 'subject', 'exam_date', 'session', 'is_rescheduled', 'is_cancelled')
    list_filter = ('exam_class__exam__school', 'exam_date', 'session', 'is_rescheduled', 'is_cancelled')
    search_fields = ('exam_class__exam__name', 'subject__subject__name')

@admin.register(EventClass, site=admin_site)
class EventClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'class_obj', 'is_active')
    list_filter = ('event__school', 'class_obj', 'is_active')
    search_fields = ('event__title', 'class_obj__class_name')
