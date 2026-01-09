from django.contrib import admin
from .models import AccountType, Account


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'account_type', 'is_postable', 'is_active')
    list_filter = ('company', 'account_type', 'is_active')
    search_fields = ('code', 'name')
