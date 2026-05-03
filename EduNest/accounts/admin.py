from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users
from webapp.admin import admin_site

class UsersAdmin(UserAdmin):
    model=Users

    list_display = ["id", "username", "role", "school", "is_super_admin", "is_active"]
    list_filter = ["username", "role", "school", "is_super_admin"]

    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {
            "fields": (
                "role",
                "school",
                "is_super_admin",
                "phone_number",
                "alternative_phone_number",
                "profile_picture",
                "aadhaar_number",
                "nationality",
                "passport",
                "date_of_birth",
                "gender",
                "blood_group",
                "marital_status",
                "is_email_verified",
                "is_phone_verified",
                "is_deleted",
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {
            "fields": (
                "role",
                "school",
                "is_super_admin",
                "phone_number",
                "email",
            )
        }),
    )

# admin.site.register(Users, UsersAdmin)
admin_site.register(Users, UsersAdmin)