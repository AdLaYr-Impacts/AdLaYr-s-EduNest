from django.db import models
from django.contrib.auth.models import AbstractUser
from common.choices import (
    UserRoles,
    UserGender,
    MaritalStatus,
)
from django_countries.fields import CountryField

class Users(AbstractUser):
    
    role = models.CharField(max_length=20, choices=UserRoles.choices)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    alternative_phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    aadhaar_number = models.CharField(max_length=12, null=True, blank=True)
    nationality = CountryField(null=True, blank=True)
    passport = models.CharField(max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=255, choices=UserGender.choices, null=True, blank=True)
    blood_group = models.CharField(max_length=255, null=True, blank=True)
    marital_status = models.CharField(max_length=255, null=True, blank=True, choices=MaritalStatus.choices)
    # school = models.ForeignKey("School", on_delete=models.CASCADE, related_name="users") # multi school suuport
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"[{self.id}] {self.username}: {self.role}"