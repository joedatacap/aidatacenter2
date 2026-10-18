"""Conservative field gates supplement excerpt matching and the model auditor."""
import re
from datetime import date
from decimal import Decimal,InvalidOperation

NUMBER=re.compile(r'(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\d.])\s*(billion|million|thousand|bn|mm|b\b|m\b)?',re.I)
SCALE={'billion':10**9,'bn':10**9,'b':10**9,'million':10**6,'mm':10**6,'m':10**6,'thousand':1000}


def amount_supported(value,excerpts):
    wanted=Decimal(str(value))
    if not wanted.is_finite():
        return False
    for text in excerpts:
        global_scale=1
        heading=re.search(r'\bin\s+(?:u\.?s\.?\s*dollars?\s+)?(millions|thousands|billions)\b',text,re.I)
        if heading:
            global_scale=SCALE[heading.group(1).lower().rstrip('s')]
        for match in NUMBER.finditer(text):
            if text[match.end():].lstrip().startswith(('%','bps','basis points')):
                continue
            number=Decimal(match.group(1).replace(',',''))
            scale=SCALE.get((match.group(2) or '').lower(),global_scale)
            if number*scale==wanted:
                return True
    return False


def date_supported(value,evidence,allow_filing_period=False):
    try:
        stamp=date.fromisoformat(str(value))
    except ValueError:
        return False
    forms=[stamp.isoformat(),stamp.strftime('%B ')+str(stamp.day)+' '+str(stamp.year),
           stamp.strftime('%b ')+str(stamp.day)+' '+str(stamp.year),
           str(stamp.month)+'/'+str(stamp.day)+'/'+str(stamp.year)]
    for source in evidence:
        text=source['excerpt'].replace(',','').lower()
        if any(form.lower() in text for form in forms):
            return True
        if allow_filing_period and stamp.strftime('%Y%m%d') in source['source_url']:
            return True
    return False


def validate_instrument_fields(candidate,evidence):
    item=dict(candidate)
    quotes=[e['excerpt'] for e in evidence]
    warnings=[]
    for field in ('outstanding_principal','commitment_amount','drawn_amount','hedge_notional'):
        value=item.get(field)
        if value is None:
            continue
        try:
            supported=amount_supported(value,quotes)
        except (InvalidOperation,ValueError):
            supported=False
        if field=='outstanding_principal':
            supported=supported and any(re.search(r'outstanding|carrying amount|principal balance|borrowings',q,re.I) for q in quotes)
        if field in ('commitment_amount','drawn_amount') and re.search(r'notes?|bonds?',item.get('name',''),re.I):
            supported=False  # Original note issuance is not a loan-facility commitment.
        if field=='drawn_amount':
            supported=supported and any(re.search(r'\bdrawn\b|\bdrawdowns?\b',q,re.I) for q in quotes)
        if not supported:
            item[field]=None
            warnings.append(field+': quoted amount/units or balance classification not supported; kept unknown.')
    for field in ('issue_date','maturity','snapshot_date','hedge_effective_date','hedge_end_date'):
        if item.get(field) is not None and not date_supported(item[field],evidence,field=='snapshot_date'):
            item[field]=None
            warnings.append(field+': exact date not supported; kept unknown.')
    coupon=item.get('coupon_pct')
    if coupon is not None:
        supported=False
        try:
            for quote in quotes:
                if re.search(r'effective\s+interest\s+rates?',quote,re.I):
                    continue  # Table yields/rates cannot establish a contractual coupon.
                for match in re.finditer(r'(\d+(?:\.\d+)?)\s*%',quote):
                    if Decimal(match.group(1))!=Decimal(str(coupon)):
                        continue
                    before=quote[max(0,match.start()-50):match.start()].lower()
                    after=quote[match.end():match.end()+40].lower()
                    contractual=max(before.rfind(word) for word in
                        ('coupon','stated interest','bear interest','bears interest','fixed'))
                    if before.rfind('yield')>contractual:
                        continue
                    if contractual>=0 or re.search(r'^\s*(senior|secured|convertible|fixed|notes)',after):
                        supported=True
        except InvalidOperation:
            pass
        if not supported:
            item['coupon_pct']=None
            warnings.append('coupon_pct: contractual coupon not established by excerpt; market yield is not a coupon.')
    if item.get('outstanding_principal') is not None and item.get('snapshot_date') is None:
        item['outstanding_principal']=None
        warnings.append('outstanding_principal: no supported as-of date; kept unknown.')
    if item.get('hedge_status')=='unhedged':
        if item.get('hedge_notional') is not None and Decimal(str(item['hedge_notional']))>0:
            item['hedge_status']='partial'
            warnings.append('hedge_status: disclosed positive hedge notional excludes an entirely unhedged classification.')
        elif not any(re.search(r'unhedged|not hedged|no[^.]{0,50}(?:interest rate hedg|derivative instruments|interest rate swaps)',q,re.I) for q in quotes):
            item['hedge_status']='unknown'
            warnings.append('hedge_status: absence of hedge disclosure is not proof of no hedge.')
    item['validation_warnings']=warnings
    return item
