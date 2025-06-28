from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserLocation, BusRoute, StudentProfile

class CustomUserAdmin(BaseUserAdmin):
    """Custom admin for User model"""

    # Fields to display in the admin list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)

    # Fields to display in the admin detail view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('BusTrack Info', {
            'fields': ('role', 'phone_number', 'date_of_birth', 'address',
                      'emergency_contact', 'emergency_phone', 'profile_picture',
                      'is_active_user', 'last_login_ip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Fields to display when adding a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('BusTrack Info', {
            'fields': ('role', 'email', 'first_name', 'last_name', 'phone_number')
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login_ip')

class UserLocationAdmin(admin.ModelAdmin):
    """Admin for UserLocation model"""
    list_display = ('user', 'latitude', 'longitude', 'is_online', 'last_updated')
    list_filter = ('is_online', 'last_updated')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('last_updated',)

class BusRouteAdmin(admin.ModelAdmin):
    """Admin for BusRoute model"""
    list_display = ('name', 'driver', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'driver__username')

class StudentProfileAdmin(admin.ModelAdmin):
    """Admin for StudentProfile model"""
    list_display = ('user', 'student_id', 'parent')
    list_filter = ('parent',)
    search_fields = ('user__username', 'student_id')

# Register models with admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserLocation, UserLocationAdmin)
# Temporarily disabled to fix server startup
# admin.site.register(BusRoute, BusRouteAdmin)
# admin.site.register(StudentProfile, StudentProfileAdmin)

# Customize admin site headers
admin.site.site_header = "BusTrack Administration"
admin.site.site_title = "BusTrack Admin"
admin.site.index_title = "Welcome to BusTrack Administration"
