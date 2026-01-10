from django.contrib import admin
from .models import Vendor
from .models import PurchaseRequest

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'ap_account', 'is_active')
    list_filter = ('company', 'is_active')
    search_fields = ('code', 'name')

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'project', 'cost_center', 'status')
    list_filter = ('company', 'status')
    search_fields = ('description',)
    readonly_fields = ('status',)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != PurchaseRequest.STATUS_DRAFT:
            return self.readonly_fields + (
                'company',
                'project',
                'cost_center',
                'description',
                'requested_by',
            )
        return self.readonly_fields