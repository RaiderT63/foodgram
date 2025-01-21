from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import CustomUser, UserSubscription

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
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
        'first_name',
        'last_name',
        'email',
        'username',
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
