from django.db import models
from apps.core.models import Company, TimeStampedModel
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.core.models import FiscalYear
from apps.core.models import Company
from apps.core.models import TimeStampedModel
from apps.core.services import get_next_document_number

class AccountType(models.Model):
    """
    High-level accounting classification.
    """
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"

    def __str__(self):
        return self.name


class Account(TimeStampedModel):
    """
    Chart of Account node.
    Supports hierarchy via self-relation.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name='accounts'
    )

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=255)

    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )

    is_active = models.BooleanField(default=True)
    is_postable = models.BooleanField(
        default=True,
        help_text="If false, cannot be used in journal entries"
    )

    class Meta:
        unique_together = ('company', 'code')
        ordering = ('code',)
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return f"{self.code} - {self.name}"
class JournalEntry(TimeStampedModel):
    """
    Accounting journal entry (header).
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='journal_entries'
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.PROTECT,
        related_name='journal_entries'
    )

    document_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )
    date = models.DateField()
    description = models.CharField(max_length=255)

    is_posted = models.BooleanField(default=False)

    class Meta:
        ordering = ('-date',)
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"

    def __str__(self):
        return self.document_number or "Unposted Entry"

    def clean(self):
        if self.fiscal_year.company != self.company:
            raise ValidationError("Fiscal year does not belong to company.")

    def post(self, document_type):
        """
        Finalize the journal entry.
        Generates document number and locks the entry.
        """
        if self.is_posted:
            raise ValidationError("Journal entry already posted.")

        totals = self.lines.aggregate(
            debit=Sum('debit'),
            credit=Sum('credit')
        )

        if (totals['debit'] or 0) != (totals['credit'] or 0):
            raise ValidationError("Journal entry is not balanced.")

        self.document_number = get_next_document_number(
            self.company,
            self.fiscal_year,
            document_type
        )
        self.is_posted = True
        self.save(update_fields=['document_number', 'is_posted'])


class JournalLine(models.Model):
    """
    Accounting journal line (debit/credit).
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )
    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )
    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    class Meta:
        verbose_name = "Journal Line"
        verbose_name_plural = "Journal Lines"

    def clean(self):
        if self.debit and self.credit:
            raise ValidationError("Line cannot have both debit and credit.")

        if not self.account.is_postable:
            raise ValidationError("Account is not postable.")

    def __str__(self):
        return f"{self.account} | D:{self.debit} C:{self.credit}"