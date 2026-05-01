from django.contrib import admin
from ..models import SchoolTeacher, TeacherEducationDetails, TeacherExperianceDetails, TeacherEmploymentDetails
from . import admin_site

@admin.register(SchoolTeacher, site=admin_site)
class SchoolTeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'school', 'teacher_code', 'joining_date', 'employment_type', 'status', 'is_active')
    list_filter = ('school', 'employment_type', 'status', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'teacher_code', 'school__short_name')

@admin.register(TeacherEducationDetails, site=admin_site)
class TeacherEducationDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'degree', 'specialization', 'institution_name', 'year_of_passing', 'is_active')
    list_filter = ('teacher__school', 'year_of_passing', 'is_active')
    search_fields = ('teacher__user__first_name', 'degree', 'institution_name')

@admin.register(TeacherExperianceDetails, site=admin_site)
class TeacherExperianceDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'school_name', 'designation', 'years_of_experiance', 'is_active')
    list_filter = ('teacher__school', 'is_active')
    search_fields = ('teacher__user__first_name', 'school_name', 'designation')

@admin.register(TeacherEmploymentDetails, site=admin_site)
class TeacherEmploymentDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'teacher', 'basic_salary', 'bank_name', 'bank_account_number', 'is_active')
    list_filter = ('teacher__school', 'is_active')
    search_fields = ('teacher__user__first_name', 'bank_name', 'bank_account_number')
