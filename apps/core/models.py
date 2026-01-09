from django.db import models


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
