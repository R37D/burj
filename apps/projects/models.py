from django.db import models
from apps.core.models import Company, FiscalYear, TimeStampedModel


class Project(TimeStampedModel):
    """
    Represents a construction project.
    Acts as a high-level cost & profit container.
    """
    STATUS_PLANNED = 'planned'
    STATUS_ACTIVE = 'active'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = (
        (STATUS_PLANNED, 'Planned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        on_delete=models.PROTECT,
        related_name='projects'
    )

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNED
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('company', 'code')
        ordering = ('code',)
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.code} - {self.name}"
class ProjectCostCenter(TimeStampedModel):
    """
    Work Breakdown Structure (WBS) / Cost Center within a project.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='cost_centers'
    )

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)

    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children'
    )

    is_postable = models.BooleanField(
        default=True,
        help_text="If false, cannot be used for financial postings"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('project', 'code')
        ordering = ('code',)
        verbose_name = "Project Cost Center"
        verbose_name_plural = "Project Cost Centers"

    def __str__(self):
        return f"{self.project.code} - {self.code}"
