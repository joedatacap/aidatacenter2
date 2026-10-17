from neocloud.validation import validate_instrument_fields


def evidence(text):
    return [{'excerpt':text,'source_url':'https://www.sec.gov/company-20260630.htm'}]


def test_commitment_is_not_published_as_outstanding_principal():
    item=validate_instrument_fields({'commitment_amount':'775000000','outstanding_principal':'775000000','snapshot_date':'2026-06-30'},
          evidence('The original facility commitment was $775 million.'))
    assert item['commitment_amount']=='775000000'
    assert item['outstanding_principal'] is None


def test_real_balance_units_and_dates_are_retained_but_unknown_dates_are_removed():
    item=validate_instrument_fields({'outstanding_principal':'413000000','snapshot_date':'2026-06-30','maturity':'2030-01-01'},
          evidence('Borrowings outstanding as of June 30, 2026 were $413 million. Maturity is in 2030.'))
    assert item['outstanding_principal']=='413000000'
    assert item['snapshot_date']=='2026-06-30'
    assert item['maturity'] is None


def test_secondary_yield_cannot_replace_fixed_coupon():
    text='The 9.625% senior notes have a secondary market yield of 15%.'
    assert validate_instrument_fields({'coupon_pct':'15'},evidence(text))['coupon_pct'] is None
    assert validate_instrument_fields({'coupon_pct':'9.625'},evidence(text))['coupon_pct']=='9.625'

def test_missing_hedge_disclosure_never_becomes_assumed_unhedged():
    item=validate_instrument_fields({'hedge_status':'unhedged'},evidence('The facility bears interest at SOFR plus 225 basis points.'))
    assert item['hedge_status']=='unknown'
    hedged=validate_instrument_fields({'hedge_status':'unhedged','hedge_notional':'394000000'},evidence('Interest rate swaps hedge $394 million of the facility.'))
    assert hedged['hedge_status']=='partial'
