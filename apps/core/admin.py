from django.contrib import admin
from .models import Company, Branch, FiscalYear


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
