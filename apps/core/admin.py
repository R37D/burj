from django.contrib import admin
from .models import Company, Branch, FiscalYear
from .models import SystemSettings
from .models import UserProfile, Role, RolePermission


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)
    ordering = ('name',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('company', 'is_active')
    ordering = ('company', 'name')


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'start_date', 'end_date', 'is_active')
    list_filter = ('company', 'is_active')
    ordering = ('-year',)

    def save_model(self, request, obj, form, change):
        """
        Ensure only one active fiscal year per company.
        """
        if obj.is_active:
            FiscalYear.objects.filter(
                company=obj.company,
                is_active=True
            ).exclude(pk=obj.pk).update(is_active=False)

        super().save_model(request, obj, form, change)
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('company', 'default_currency', 'decimal_places', 'is_active')
    list_filter = ('is_active',)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'branch', 'is_active')
    list_filter = ('company', 'branch', 'is_active')
    search_fields = ('user__username',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('name',)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission')
    list_filter = ('role',)
