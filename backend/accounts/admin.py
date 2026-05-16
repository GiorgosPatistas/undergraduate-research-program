from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'role', 'full_name', 'specialty', 'is_active')
    list_filter   = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'full_name')
    fieldsets     = UserAdmin.fieldsets + (
        ('Healthcare Profile', {'fields': ('role', 'full_name', 'specialty')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Healthcare Profile', {'fields': ('role', 'full_name', 'specialty')}),
    )
