from django.contrib import admin
from .models import AccountType, Account
from .models import JournalEntry, JournalLine

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'account_type', 'is_postable', 'is_active')
    list_filter = ('company', 'account_type', 'is_active')
    search_fields = ('code', 'name')

class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 1
    autocomplete_fields = ('account', 'project', 'cost_center')



@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        'document_number',
        'company',
        'date',
        'is_posted'
    )
    list_filter = ('company', 'is_posted')
    inlines = [JournalLineInline]
    readonly_fields = ('document_number',)

    def save_model(self, request, obj, form, change):
        if obj.is_posted:
            raise ValidationError("Cannot modify a posted journal entry.")
        super().save_model(request, obj, form, change)