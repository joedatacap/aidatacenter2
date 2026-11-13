from copy import deepcopy
import json
from pathlib import Path
import pytest
from neocloud.directory import build_directory
from neocloud.website_v2 import amount, build_website_v2, debt_market_cap

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def inputs():
    return (build_directory(json.loads((ROOT/'neocloud/data/debt_directory.json').read_text())),
            json.loads((ROOT/'neocloud/data/website_v2.json').read_text()))


def test_snapshot_ratio_and_no_mutation(inputs):
    base, extra = inputs
    original = deepcopy(base)
    result = build_website_v2(base, extra)
    companies = {c['ticker']:c for c in result['companies']}
    assert base == original
    assert companies['CRWV']['v2']['debt_market_cap_percent'] == 148.9
    assert companies['NBIS']['metrics']['debt']['value'] == '14190800000'
    assert companies['NBIS']['metrics']['cash']['value'] == '7425600000'
    assert '1,056' not in companies['NBIS']['metrics']['cash']['basis']
    assert companies['NBIS']['as_of'] == '2026-09-30'
    assert companies['NBIS']['v2']['debt_market_cap_percent'] is None
    assert 'debt_assets' not in companies['NBIS']['metrics']
    assert companies['GLXY']['v2']['debt_market_cap_percent'] is None
    assert companies['NSCALE']['v2']['debt_market_cap_percent'] is None
    assert companies['HIVE']['v2']['size_band'] == 'small'


@pytest.mark.parametrize('value', [True, -1, 'NaN', 'Infinity', '-Infinity', 'bad'])
def test_invalid_financial_amounts(value):
    with pytest.raises(ValueError): amount(value)


def test_ratio_boundary_and_zero_debt():
    market = dict(value=100,currency='USD',status='provider_reported',as_of='2026-11-12')
    args=dict(listing='listed',debt_date='2026-09-30')
    assert debt_market_cap(0,market,**args)==0
    assert debt_market_cap(150,market,**args)==150
    assert debt_market_cap(150,dict(market,currency='EUR'),**args) is None
    assert debt_market_cap(150,market,listing='private',debt_date='2026-09-30') is None
    assert debt_market_cap(150,market,listing='listed',debt_date='2026-12-31') is None
    assert debt_market_cap(150,dict(market,ratio_blocker='unresolved'),**args) is None
    with pytest.raises(ValueError): debt_market_cap(1,dict(market,value=0),**args)


def test_schedule_reconciles_to_principal_not_carrying(inputs):
    base, extra = inputs
    c=next(c for c in build_website_v2(base,extra)['companies'] if c['ticker']=='CRWV')
    x=c['v2'];s=x['maturity_schedule']
    assert sum(i['principal'] for i in x['debt_inventory']) == s['total'] == 47505000000
    assert int(c['metrics']['debt']['value']) == 46873000000
    assert s['total']-int(c['metrics']['debt']['value']) == 632000000
    assert '12/24/36' in s['note']
    extra['companies']['CRWV']['maturity_schedule']['buckets'][0]['value']+=1
    with pytest.raises(ValueError,match='reconcile'):build_website_v2(base,extra)


@pytest.mark.parametrize('mutation', ['source','future','private','url','duplicate','coverage'])
def test_invalid_research_cannot_publish(inputs,mutation):
    base,extra=inputs
    if mutation=='source':extra['companies']['IREN']['contracts'][0]['source_ids']=['missing']
    elif mutation=='future':extra['companies']['IREN']['contracts'][0]['as_of']='2030-01-01'
    elif mutation=='private':extra['companies']['NSCALE']['market_cap']=extra['companies']['CRWV']['market_cap']
    elif mutation=='url':extra['sources'][0]['url']='javascript:alert(1)'
    elif mutation=='duplicate':extra['sources'].append(extra['sources'][0])
    elif mutation=='coverage':extra['companies'].pop('HIVE')
    with pytest.raises(ValueError):build_website_v2(base,extra)
