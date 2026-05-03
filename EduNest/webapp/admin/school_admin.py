from django.contrib import admin
from ..models import School, SchoolContact, SchoolRegistration, Period, ExamType, Exam, Event
from . import admin_site

@admin.register(School, site=admin_site)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_name', 'school_code', 'school_type', 'board', 'medium_of_instructions', 'is_active')
    search_fields = ('name', 'short_name', 'school_code')
    list_filter = ('school_type', 'board', 'medium_of_instructions', 'is_active')

@admin.register(SchoolContact, site=admin_site)
class SchoolContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'email', 'phone_number', 'is_active')
    search_fields = ('school__short_name', 'email', 'phone_number')
    list_filter = ('is_active',)

@admin.register(SchoolRegistration, site=admin_site)
class SchoolRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'registeration_number', 'udise_code', 'is_active')
    search_fields = ('school__short_name', 'registeration_number', 'udise_code')
    list_filter = ('is_active',)

@admin.register(Period, site=admin_site)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('id', 'school', 'class_obj', 'name', 'start_time', 'end_time', 'is_break', 'order')
    list_filter = ('school', 'class_obj', 'is_break')
    search_fields = ('name', 'school__short_name')

@admin.register(ExamType, site=admin_site)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('name', 'school__short_name')

@admin.register(Exam, site=admin_site)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school', 'exam_type', 'start_date', 'end_date', 'status', 'is_locked')
    list_filter = ('school', 'exam_type', 'status', 'is_locked')
    search_fields = ('name', 'school__short_name')

@admin.register(Event, site=admin_site)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'school', 'category', 'type', 'start_datetime', 'end_datetime', 'is_active')
    list_filter = ('school', 'category', 'type', 'is_active')
    search_fields = ('title', 'school__short_name')
