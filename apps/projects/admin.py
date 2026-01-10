from django.contrib import admin
from .models import Project
from .models import ProjectCostCenter

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'fiscal_year', 'status', 'is_active')
    list_filter = ('company', 'fiscal_year', 'status', 'is_active')
    search_fields = ('code', 'name')
@admin.register(ProjectCostCenter)
class ProjectCostCenterAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'project',
        'parent',
        'is_postable',
        'is_active'
    )
    list_filter = ('project', 'is_postable', 'is_active')
    search_fields = ('code', 'name')