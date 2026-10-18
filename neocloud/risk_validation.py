"""Fail-closed numeric/source gates before AI review of V2 records."""
import re
from decimal import Decimal
from .validation import amount_supported, date_supported

MONEY = {'amount', 'market_cap', 'annual_minimum', 'guarantee_cap', 'prepayment',
         'adjusted_ebitda', 'cash_interest', 'interest_expense', 'capitalized_interest',
         'revenue', 'cfo', 'maintenance_capex', 'growth_capex', 'gross_debt', 'unrestricted_cash', 'equity_market_cap', 'rate_sensitive_principal'}


def validate_risk_record(kind, item, evidence):
    by_id = {e['id']: e for e in evidence}
    def cited(record, key='evidence_ids'):
        return [by_id[e] for e in record.get(key, []) if e in by_id]
    def check(record):
        citations = cited(record)
        if not citations:
            raise ValueError('Missing matched source evidence')
        texts = [e['excerpt'] for e in citations]
        for field in MONEY:
            if record.get(field) is None:
                continue
            field_texts = [e['excerpt'] for e in cited(record, 'market_cap_evidence_ids')] if field == 'market_cap' else texts
            if not amount_supported(abs(Decimal(str(record[field]))), field_texts):
                raise ValueError('Amount or units not supported: ' + field)
        for field in ('market_yield_pct', 'treasury_yield_pct'):
            if record.get(field) is None:
                continue
            field_texts = [e['excerpt'] for e in cited(record, 'treasury_evidence_ids')] if field == 'treasury_yield_pct' else texts
            if not any(Decimal(m.group(1)) == Decimal(str(record[field]))
                       for text in field_texts for m in re.finditer(r'(\d+(?:\.\d+)?)\s*%', text)):
                raise ValueError('Yield percentage not supported')
        return texts
    texts = check(item)
    if kind == 'funding_plans':
        for line in item.get('lines', []):
            check(line)
    if kind == 'cash_flows':
        for field in ('period_start', 'period_end'):
            if not date_supported(item[field], cited(item)):
                raise ValueError('TTM period not supported')
    if kind == 'bond_quotes':
        if not any(item['security_id'].lower() in text.lower() for text in texts):
            raise ValueError('Specific security identity not supported')
        if not date_supported(str(item['quoted_at'])[:10], cited(item)):
            raise ValueError('Quote date not supported')
    if kind == 'contracts':
        joined = ' '.join(texts).lower()
        for field in ('project', 'customer', 'guarantor'):
            if item.get(field) and item[field].lower() not in joined:
                raise ValueError('Contract relationship not supported: ' + field)
        if (item.get('guarantor') or '').lower() == 'google':
            scope = item.get('covered_obligations', '').lower()
            if not re.search(r'lease|pass.through', scope) or re.search(r'guarantees? all|covers? all (?:hut|corporate|parent)', scope):
                raise ValueError('Google support must preserve limited lease scope')
    if kind == 'repayments':
        if item['precision'] == 'day':
            if not date_supported(item['due_start'], cited(item)):
                raise ValueError('Exact maturity date unsupported')
        elif not all(str(item[field])[:4] in ' '.join(texts) for field in ('due_start', 'due_end')):
            raise ValueError('Maturity bucket unsupported')
    return item
