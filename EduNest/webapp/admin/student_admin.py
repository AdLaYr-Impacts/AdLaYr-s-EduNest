from django.contrib import admin
from ..models import (
    Students, StudentsAdmissionDetails, StudentParentDetails, StudentAcademicdetails, 
    StudentAttendance, Mark, StudentMark, EventResponse, Fee, Payment, FeeReminder, FeeWarning
)
from . import admin_site

@admin.register(Students, site=admin_site)
class StudentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'school', 'religion', 'caste_category', 'is_active')
    list_filter = ('school', 'caste_category', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'school__short_name')

@admin.register(StudentsAdmissionDetails, site=admin_site)
class StudentsAdmissionDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'admission_number', 'admission_type', 'admission_date', 'student_status', 'is_active')
    list_filter = ('student__school', 'admission_type', 'student_status', 'is_active')
    search_fields = ('student__user__first_name', 'admission_number')

@admin.register(StudentParentDetails, site=admin_site)
class StudentParentDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'father_name', 'father_phone', 'mother_name', 'mother_phone', 'is_active')
    list_filter = ('student__school', 'is_active')
    search_fields = ('student__user__first_name', 'father_name', 'mother_name')

@admin.register(StudentAcademicdetails, site=admin_site)
class StudentAcademicdetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'student_class', 'roll_number', 'register_number', 'is_active')
    list_filter = ('student_class__school', 'student_class', 'is_active')
    search_fields = ('student__user__first_name', 'roll_number', 'register_number')

@admin.register(StudentAttendance, site=admin_site)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'student', 'status', 'is_active')
    list_filter = ('session__class_obj__school', 'status', 'is_active')
    search_fields = ('student__user__first_name', 'session__date')

@admin.register(Mark, site=admin_site)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam_class', 'student', 'total_marks', 'out_of_marks', 'result', 'status')
    list_filter = ('exam_class__exam__school', 'result', 'status')
    search_fields = ('student__user__first_name', 'exam_class__exam__name')

@admin.register(StudentMark, site=admin_site)
class StudentMarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam_schedule', 'student_exam', 'marks_obtained', 'is_absent', 'is_active')
    list_filter = ('exam_schedule__exam_class__exam__school', 'is_absent', 'is_active')
    search_fields = ('student_exam__student__user__first_name', 'exam_schedule__subject__subject__name')

@admin.register(EventResponse, site=admin_site)
class EventResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_obj', 'student', 'status', 'responed_by', 'responded_at', 'is_active')
    list_filter = ('event_obj__school', 'status', 'responed_by', 'is_active')
    search_fields = ('student__user__first_name', 'event_obj__title')

@admin.register(Fee, site=admin_site)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'fee_name', 'total_amount', 'last_due_date', 'is_active')
    list_filter = ('student__school', 'last_due_date', 'is_active')
    search_fields = ('student__user__first_name', 'fee_name')

@admin.register(Payment, site=admin_site)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'fee', 'amount', 'payment_date', 'payment_method', 'status', 'is_active')
    list_filter = ('fee__student__school', 'payment_method', 'status', 'is_active')
    search_fields = ('fee__student__user__first_name', 'fee__fee_name')

@admin.register(FeeReminder, site=admin_site)
class FeeReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'fee', 'reminder_date', 'amount', 'is_active')
    list_filter = ('fee__student__school', 'reminder_date', 'is_active')
    search_fields = ('fee__student__user__first_name', 'fee__fee_name')

@admin.register(FeeWarning, site=admin_site)
class FeeWarningAdmin(admin.ModelAdmin):
    list_display = ('id', 'fee', 'type', 'is_active')
    list_filter = ('fee__student__school', 'type', 'is_active')
    search_fields = ('fee__student__user__first_name', 'fee__fee_name')
