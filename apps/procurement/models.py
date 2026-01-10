from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core.models import Company, TimeStampedModel, DocumentType
from apps.core.services import get_next_document_number
from apps.finance.models import Account
from apps.projects.models import Project, ProjectCostCenter

User = get_user_model()

# =========================================================
# Vendor
# =========================================================

class Vendor(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='vendors'
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    ap_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='vendors',
        help_text="Accounts Payable control account (e.g. 2100)"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'code')
        ordering = ('code',)
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if not self.ap_account.is_control:
            raise ValidationError("AP account must be a control account.")


# =========================================================
# Purchase Request
# =========================================================

class PurchaseRequest(TimeStampedModel):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name='purchase_requests'
    )

    cost_center = models.ForeignKey(
        ProjectCostCenter,
        on_delete=models.PROTECT,
        related_name='purchase_requests'
    )

    description = models.CharField(max_length=255)

    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='purchase_requests'
    )

    request_date = models.DateField(null=True, blank=True)
    estimated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Purchase Request"
        verbose_name_plural = "Purchase Requests"

    def __str__(self):
        return f"PR-{self.id}"

    def clean(self):
        if not self.cost_center.is_postable:
            raise ValidationError("Cost center is not postable.")
        if self.cost_center.project != self.project:
            raise ValidationError("Cost center does not belong to project.")
        if self.project.company != self.company:
            raise ValidationError("Project does not belong to company.")

    def submit(self):
        if self.status != self.STATUS_DRAFT:
            raise ValidationError("Only draft PR can be submitted.")
        self.status = self.STATUS_SUBMITTED
        self.save(update_fields=['status'])

    def approve(self):
        if self.status != self.STATUS_SUBMITTED:
            raise ValidationError("Only submitted PR can be approved.")
        self.status = self.STATUS_APPROVED
        self.save(update_fields=['status'])

    def reject(self):
        if self.status != self.STATUS_SUBMITTED:
            raise ValidationError("Only submitted PR can be rejected.")
        self.status = self.STATUS_REJECTED
        self.save(update_fields=['status'])

    @property
    def can_create_po(self):
        return self.status == self.STATUS_APPROVED


# =========================================================
# Purchase Order
# =========================================================

class PurchaseOrder(TimeStampedModel):
    STATUS_DRAFT = 'draft'
    STATUS_ISSUED = 'issued'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_CLOSED, 'Closed'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )

    purchase_request = models.OneToOneField(
        PurchaseRequest,
        on_delete=models.PROTECT,
        related_name='purchase_order'
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )

    document_number = models.CharField(max_length=50, blank=True, editable=False)
    order_date = models.DateField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    issued_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"

    def issue(self):
        if self.status != self.STATUS_DRAFT:
            raise ValidationError("Only draft PO can be issued.")

        fiscal_year = self.purchase_request.project.fiscal_year
        doc_type = DocumentType.objects.get(code='PO')

        self.document_number = get_next_document_number(
            company=self.company,
            fiscal_year=fiscal_year,
            document_type=doc_type
        )

        self.status = self.STATUS_ISSUED
        self.issued_at = timezone.now()
        self.save()


# =========================================================
# Goods Receipt
# =========================================================

class GoodsReceipt(TimeStampedModel):
    STATUS_DRAFT = 'draft'
    STATUS_POSTED = 'posted'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_POSTED, 'Posted'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='goods_receipts'
    )

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='goods_receipts'
    )

    document_number = models.CharField(max_length=50, blank=True, editable=False)
    receipt_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Goods Receipt"
        verbose_name_plural = "Goods Receipts"

    @transaction.atomic
    def post(self):
        if self.status != self.STATUS_DRAFT:
            raise ValidationError("Only draft GR can be posted.")

        fiscal_year = self.purchase_order.purchase_request.project.fiscal_year
        gr_type = DocumentType.objects.get(code='GR')

        self.document_number = get_next_document_number(
            company=self.company,
            fiscal_year=fiscal_year,
            document_type=gr_type
        )

        self.status = self.STATUS_POSTED
        self.posted_at = timezone.now()
        self.save()

        self._post_grni_entry(fiscal_year)

    def _post_grni_entry(self, fiscal_year):
        from apps.finance.models import JournalEntry, JournalLine

        je_type = DocumentType.objects.get(code='JE')

        entry = JournalEntry.objects.create(
            company=self.company,
            fiscal_year=fiscal_year,
            document_number=get_next_document_number(
                company=self.company,
                fiscal_year=fiscal_year,
                document_type=je_type
            ),
            date=self.receipt_date,
            description=f"Goods Receipt {self.document_number}",
            is_posted=True
        )

        vendor = self.purchase_order.vendor

        JournalLine.objects.create(
            journal_entry=entry,
            account=vendor.ap_account,
            debit=self.amount,
            credit=0
        )

        JournalLine.objects.create(
            journal_entry=entry,
            account=vendor.ap_account,
            debit=0,
            credit=self.amount
        )


# =========================================================
# Vendor Invoice
# =========================================================

class VendorInvoice(TimeStampedModel):
    STATUS_DRAFT = 'draft'
    STATUS_POSTED = 'posted'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_POSTED, 'Posted'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='vendor_invoices'
    )

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name='invoices'
    )

    goods_receipt = models.OneToOneField(
        GoodsReceipt,
        on_delete=models.PROTECT,
        related_name='vendor_invoice'
    )

    document_number = models.CharField(max_length=50, blank=True, editable=False)
    invoice_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Vendor Invoice"
        verbose_name_plural = "Vendor Invoices"

    @transaction.atomic
    def post(self):
        if self.status != self.STATUS_DRAFT:
            raise ValidationError("Only draft invoices can be posted.")

        fiscal_year = self.goods_receipt.purchase_order.purchase_request.project.fiscal_year
        vi_type = DocumentType.objects.get(code='VI')

        self.document_number = get_next_document_number(
            company=self.company,
            fiscal_year=fiscal_year,
            document_type=vi_type
        )

        self.status = self.STATUS_POSTED
        self.posted_at = timezone.now()
        self.save()

        self._post_ap_entry(fiscal_year)

    def _post_ap_entry(self, fiscal_year):
        from apps.finance.models import JournalEntry, JournalLine

        je_type = DocumentType.objects.get(code='JE')

        entry = JournalEntry.objects.create(
            company=self.company,
            fiscal_year=fiscal_year,
            document_number=get_next_document_number(
                company=self.company,
                fiscal_year=fiscal_year,
                document_type=je_type
            ),
            date=self.invoice_date,
            description=f"Vendor Invoice {self.document_number}",
            is_posted=True
        )

        JournalLine.objects.create(
            journal_entry=entry,
            account=self.vendor.ap_account,
            debit=self.amount,
            credit=0
        )

        JournalLine.objects.create(
            journal_entry=entry,
            account=self.vendor.ap_account,
            debit=0,
            credit=self.amount
        )
