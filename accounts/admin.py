from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, NGOProfile, LawyerProfile, DonorProfile

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'role', 'is_staff', 'is_active', 'is_verified')
    list_filter = ('role', 'is_staff', 'is_active', 'is_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role', 'phone_number', 'is_verified', 'verification_code')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'phone_number', 'password1', 'password2', 'is_verified')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, UserAdmin)

@admin.register(NGOProfile)
class NGOProfileAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'user', 'registration_number', 'is_verified')
    search_fields = ('organization_name', 'registration_number')
    list_filter = ('is_verified',)

@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'license_number', 'specialization', 'is_verified', 'rating')
    search_fields = ('full_name', 'license_number', 'specialization')
    list_filter = ('is_verified', 'is_available')

@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'allow_anonymous')
    search_fields = ('display_name',)
    list_filter = ('allow_anonymous',)
