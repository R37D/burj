from django.db import models
from apps.core.models import Company, TimeStampedModel


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
