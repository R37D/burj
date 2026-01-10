from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'fiscal_year', 'status', 'is_active')
    list_filter = ('company', 'fiscal_year', 'status', 'is_active')
    search_fields = ('code', 'name')
