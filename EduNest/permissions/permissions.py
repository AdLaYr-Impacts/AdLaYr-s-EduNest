from rest_framework.permissions import BasePermission
from common.choices import UserRoles

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.SUPER_ADMIN and
            request.user.is_super_admin
        )
    
class IsSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.SCHOOL_ADMIN
        )
    
class IsClassTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.CLASS_TEACHER
        )
    
class IsSubjectTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.SUBJECT_TEACHER
        )
    
class IsParent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.PARENT
        )
    
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active and
            not request.user.is_deleted and
            request.user.role == UserRoles.STUDENT
        )