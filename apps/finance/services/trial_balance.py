from django.db.models import Sum
from apps.finance.models import JournalLine, Account


def get_trial_balance(company, fiscal_year):
    lines = (
        JournalLine.objects
        .filter(
            journal_entry__company=company,
            journal_entry__fiscal_year=fiscal_year,
            journal_entry__is_posted=True
        )
        .values('account')
        .annotate(
            debit=Sum('debit'),
            credit=Sum('credit')
        )
    )

    results = []
    for row in lines:
        account = Account.objects.get(id=row['account'])
        results.append({
            'account_code': account.code,
            'account_name': account.name,
            'debit': row['debit'] or 0,
            'credit': row['credit'] or 0,
        })

    return results
