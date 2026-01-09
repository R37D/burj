from django.db import models
from django.contrib.auth.models import User, Permission

class TimeStampedModel(models.Model):
    """
    Abstract base model with created & updated timestamps.
    Used across all ERP domains.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    """
    Represents a legal company entity.
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    tax_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Branch(TimeStampedModel):
    """
    Represents a branch belonging to a company.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name='branches'
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'code')
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.company.code} - {self.name}"


class FiscalYear(TimeStampedModel):
    """
    Represents a fiscal year for a company.
    Only one fiscal year can be active per company.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='fiscal_years'
    )
    year = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('company', 'year')
        ordering = ['-year']
        verbose_name = "Fiscal Year"
        verbose_name_plural = "Fiscal Years"

    def __str__(self):
        return f"{self.company.code} - {self.year}"
class SystemSettings(TimeStampedModel):
    """
    Company-level system configuration.
    Only one settings record should exist per company.
    """
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # General
    default_currency = models.CharField(
        max_length=10,
        default='SAR',
        help_text="ISO currency code (e.g., SAR, USD)"
    )
    decimal_places = models.PositiveSmallIntegerField(
        default=2
    )

    date_format = models.CharField(
        max_length=20,
        default='YYYY-MM-DD'
    )

    # Document numbering
    document_start_number = models.PositiveIntegerField(
        default=1
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"Settings - {self.company.code}"
class UserProfile(TimeStampedModel):
    """
    Operational context for a user.
    Defines which company/branch the user belongs to.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} ({self.company.code})"


class Role(TimeStampedModel):
    """
    Company-scoped role.
    Example: Accountant, Project Manager, HR Officer
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='roles'
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'name')
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return f"{self.company.code} - {self.name}"


class RolePermission(models.Model):
    """
    Maps roles to Django permissions.
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"

    def __str__(self):
        return f"{self.role} -> {self.permission.codename}"
class DocumentType(TimeStampedModel):
    """
    Represents a logical document type.
    Example: Invoice, Journal Voucher, Purchase Order
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Document Type"
        verbose_name_plural = "Document Types"

    def __str__(self):
        return f"{self.code} - {self.name}"


class DocumentSequence(TimeStampedModel):
    """
    Controls document numbering per company, fiscal year, and document type.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='document_sequences'
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.CASCADE,
        related_name='document_sequences'
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE,
        related_name='sequences'
    )

    prefix = models.CharField(
        max_length=50,
        help_text="Example: BURJ-INV-2026"
    )
    last_number = models.PositiveIntegerField(default=0)
    padding = models.PositiveSmallIntegerField(default=6)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'fiscal_year', 'document_type')
        verbose_name = "Document Sequence"
        verbose_name_plural = "Document Sequences"

    def __str__(self):
        return f"{self.prefix}"
