from django.db import transaction
from .models import DocumentSequence


def get_next_document_number(company, fiscal_year, document_type):
    """
    Safely generate the next document number.
    Thread-safe and transaction-safe.
    """
    with transaction.atomic():
        sequence = DocumentSequence.objects.select_for_update().get(
            company=company,
            fiscal_year=fiscal_year,
            document_type=document_type,
            is_active=True
        )

        sequence.last_number += 1
        sequence.save(update_fields=['last_number'])

        number = str(sequence.last_number).zfill(sequence.padding)
        return f"{sequence.prefix}-{number}"
