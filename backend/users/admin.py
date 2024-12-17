from django.contrib import admin

from .models import CustomUser, UserSubscription


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'is_active',
    )
    search_fields = (
        'email',
        'username',
    )
    list_editable = (
        'first_name',
        'last_name',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
    )
    ordering = (
        'email',
    )
    readonly_fields = (
        'last_login',
        'date_joined',
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscriber',
        'author',
    )
    search_fields = (
        'subscriber__username',
        'author__username',
    )
    list_filter = (
        'subscriber',
        'author',
    )
    ordering = (
        'subscriber',
    )
