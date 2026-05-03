from django.contrib import admin
from ..models import AddressBook
from . import admin_site

@admin.register(AddressBook, site=admin_site)
class AddressBookAdmin(admin.ModelAdmin):
    list_display = ('id', 'address_type', 'user', 'school', 'city', 'state', 'is_active')
    list_filter = ('address_type', 'state', 'is_active')
    search_fields = ('user__first_name', 'school__short_name', 'city', 'state')
