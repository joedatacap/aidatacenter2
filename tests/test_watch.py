"""Financial and import boundaries for the connected Watch snapshot."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from neocloud.directory import build_directory
from neocloud.website_v2 import build_website_v2
from neocloud.watch import (FOCUS,build_watch,consensus_surprise,guidance_change,import_earnings_watch,
    market_cap_band,market_reaction,percentage_change,quarter_from_ytd,stage_changes)

ROOT=Path(__file__).resolve().parents[1]


def fact(value,**overrides):
    return dict({'id':'a','value':value,'scope':'consolidated','currency':'USD','unit':'USD','months':3,'accounting_basis':'GAAP','source_ids':['s']},**overrides)


def test_negative_missing_and_noncomparable_growth():
    assert percentage_change(fact(5),fact(0))['value'] is None
    assert percentage_change(fact(5),fact(-2))['absolute_change']==7
    assert percentage_change(fact(None),fact(2))['status']=='not_researched'
    assert percentage_change(fact(4),fact(2,scope='GPU segment'))['status']=='not_applicable'
    result=percentage_change(fact(4),fact(2))
    assert result['value']==100 and result['input_ids']==['a','a']
    assert result['formula']=='percentage_change/v1'


def test_ytd_cash_flow_must_not_masquerade_as_quarter():
    first=fact(-30,period_type='ytd',fiscal_year='2026',fiscal_year_start='2026-01-01',metric='operating_cash_flow',period_end='2026-03-31')
    second=dict(first,id='b',months=6,value=-12,period_end='2026-06-30')
    result=quarter_from_ytd(second,first)
    assert result['value']==18 and result['months']==3 and result['period_type']=='quarter'
    for changed in [dict(second,fiscal_year='2025'),dict(second,months=9),dict(second,currency='EUR')]:
        with pytest.raises(ValueError):quarter_from_ytd(changed,first)


def test_guidance_same_basis_and_original_history():
    old=dict(id='old',metric='revenue',currency='USD',unit='USD',scope='group',accounting_basis='GAAP',period_start='2026-01-01',period_end='2026-12-31',as_of='2026-08-01',low=100,high=120)
    new=dict(old,id='new',as_of='2026-11-01',low=120,high=140)
    result=guidance_change(old,new)
    assert result['classification']=='raised' and result['input_ids']==['old','new']
    assert old['low']==100
    assert guidance_change(old,dict(new,scope='segment'))['classification']=='not_comparable'
    assert guidance_change(old,dict(new,accounting_basis='adjusted'))['classification']=='not_comparable'
    assert guidance_change(dict(old,low=-10,high=0),new)['percent_change'] is None


def test_consensus_requires_pre_release_time_and_gaap_alignment():
    actual=fact(10,metric='eps',period_end='2026-09-30')
    estimate=dict(actual,id='estimate',value=8,observed_at='2026-11-09T15:00:00Z')
    assert consensus_surprise(actual,estimate,'2026-11-10T21:00:00Z')['value']==25
    assert consensus_surprise(actual,dict(estimate,accounting_basis='adjusted'),'2026-11-10T21:00:00Z')['value'] is None
    with pytest.raises(ValueError):consensus_surprise(actual,dict(estimate,observed_at='2026-11-11T15:00:00Z'),'2026-11-10T21:00:00Z')
    with pytest.raises(ValueError):consensus_surprise(actual,dict(estimate,observed_at='2026-11-09T15:00:00'),'2026-11-10T21:00:00Z')


def test_market_return_windows_and_split_treatment():
    before=dict(id='pre',value=10,currency='USD',ticker='AGPU',split_adjusted=True,basis='price_return',closed_at='2026-11-13T21:00:00Z',session='2026-11-13',source_ids=['p'])
    after=dict(before,id='post',value=11,session='2026-11-17',closed_at='2026-11-17T21:00:00Z')
    kwargs=dict(horizon='T+1',release_at='2026-11-16T21:30:00Z',first_session='2026-11-17',fifth_session='2026-11-23',pre_release_session='2026-11-13')
    assert round(market_reaction(before,after,**kwargs)['value'],4)==10
    with pytest.raises(ValueError):market_reaction(before,dict(after,split_adjusted=False),**kwargs)
    with pytest.raises(ValueError):market_reaction(before,dict(after,session='2026-11-19'),**kwargs)
    with pytest.raises(ValueError):market_reaction(before,after,**dict(kwargs,horizon='T+3'))


def test_reference_aliases_missing_name_stale_metadata_and_no_private_import():
    raw={'updated':'2026-11-16 12:41','as_of':'2026-08-21','stale':False,'aethir_bridge':'PRIVATE-CANARY',
         'delta':['UNREVIEWED-VERDICT'],'earnings':{'reported':[{'ticker':'AGPU','date':'2026-08-14','rev':'$3.2M with mixed scope',
         'rev_vs':'unverified expectation','net_loss':'-$3M','drift_3d':'+7%','verdict':'beat','call_takeaway':'INTERNAL-CANARY'}]}}
    normalized=import_earnings_watch(raw,source_commit='abc',source_path='password/neocloud/data.json')
    row=normalized['candidates'][0]
    assert row['company']=='Axe Compute' and row['period_end'] is None
    assert row['candidate_fields']['loss']=='-$3M' and row['candidate_fields']['rev_vs_consensus']=='unverified expectation'
    assert row['market_reaction']['T+1']['value'] is None and row['market_reaction']['T+3_imported']=='+7%'
    assert normalized['metadata']['timezone']=='not_established'
    assert normalized['metadata']['raw_as_of']=='2026-08-21'
    encoded=json.dumps(normalized)
    assert all(word not in encoded for word in ('PRIVATE-CANARY','INTERNAL-CANARY','UNREVIEWED-VERDICT'))
    assert 'value' not in row['candidate_fields'] # free text never becomes a financial number
    assert normalized==import_earnings_watch(raw,source_commit='abc',source_path='password/neocloud/data.json')
    amended=deepcopy(raw);amended['earnings']['reported'][0]['rev']='$3.3M amended'
    changed=import_earnings_watch(amended,source_commit='abc',source_path='password/neocloud/data.json')
    assert changed['candidates'][0]['id']==row['id']
    delta=stage_changes(normalized,changed,'2026-11-16')['changes']
    assert len(delta)==1 and delta[0]['kind']=='changed'
    assert delta[0]['old']['candidate_fields']['rev']=='$3.2M with mixed scope'
    raw['earnings']['reported']*=2
    assert len(import_earnings_watch(raw)['candidates'])==1


def test_refresh_is_idempotent_and_expired_events_reconcile():
    candidate={'candidates':[{'id':'x','status':'pending_review'}],'events':[{'date':'2026-08-14','status':'confirmed'}]}
    assert stage_changes(candidate,candidate,'2026-11-16')['changes']==[]
    result=stage_changes({'candidates':[]},candidate,'2026-11-16')
    assert result['changes'][0]['status']=='pending_review'
    assert result['expired_events'][0]['status']=='needs_reconciliation'


@pytest.mark.parametrize('value,expected',[(None,'unknown'),(89_370_000,'micro'),(300_000_000,'small'),(2_000_000_000,'mid'),(10_000_000_000,'large')])
def test_size_is_independent_from_selected_cohort(value,expected):
    assert market_cap_band(value)==expected


def base():
    directory=build_directory(json.loads((ROOT/'neocloud/data/debt_directory.json').read_text()))
    return build_website_v2(directory,json.loads((ROOT/'neocloud/data/website_v2.json').read_text()))


def research():
    return {'reviewed_at':'2026-11-16','sources':[dict(id='s',title='Issuer',url='https://issuer.example/report',published_at='2026-11-10',retrieved_at='2026-11-16',excerpt='Reported quarterly revenue.')],
        'companies':[dict(id=t.lower(),ticker=t,name=t,latest_report_status='source_access_limited',quarters=[]) for t in FOCUS]}


def test_merge_preserves_existing_financing_and_all_nine():
    original=base();before=deepcopy(original)
    result=build_watch(original,[research()])
    assert original==before and len(result['companies'])==19
    by_ticker={c['ticker']:c for c in result['companies']}
    assert by_ticker['IREN']['focus_group']=='benchmark'
    assert by_ticker['IREN']['market_cap_band']=='mid'
    for existing in original['companies']:assert by_ticker[existing['ticker']]['financing']==existing
    assert by_ticker['NBIS']['financing']['v2']['debt_market_cap_percent'] is None
    assert by_ticker['HUT']['financing']['v2']['maturity_schedule']['timing_issue']


def test_source_and_period_validation_are_not_optional():
    r=research();r['companies'][0]['quarters']=[dict(id='crwv-q3',period_end='2026-09-30',release_date='2026-11-10',fiscal_label='Q3 2026',months=3,metrics={'revenue':dict(fact(100),definition='Recognized revenue',status='reported')})]
    build_watch(base(),[r])
    with pytest.raises(ValueError,match='YTD'):
        changed=deepcopy(r);changed['companies'][0]['quarters'][0].update(months=9,period_type='quarter');build_watch(base(),[changed])
    with pytest.raises(ValueError,match='source'):
        changed=deepcopy(r);changed['companies'][0]['quarters'][0]['metrics']['revenue']['source_ids']=['not-present'];build_watch(base(),[changed])
    with pytest.raises(ValueError,match='Unsafe'):
        changed=deepcopy(r);changed['sources'][0]['url']='javascript:alert(1)';build_watch(base(),[changed])
    with pytest.raises(ValueError,match='nine'):
        changed=deepcopy(r);changed['companies'].pop();build_watch(base(),[changed])


def test_market_only_enrichment_keeps_history_and_ratio_blocker():
    r=research();m={'reviewed_at':'2026-11-16','sources':[], 'companies':[{'id':'nbis','ticker':'NBIS','market_observation':{'value':33_960_000_000,'status':'provider_reported','currency':'USD','as_of':'2026-11-13','source_ids':['s'],'ratio_blocker':'Share classes unresolved'}}]}
    result=build_watch(base(),[r,m]);nbis=next(c for c in result['companies'] if c['ticker']=='NBIS')
    assert nbis['market_cap']['as_of']=='2026-11-13'
    assert nbis['financing']['v2']['debt_market_cap_percent'] is None
    assert nbis['freshness']['market_data']=='2026-11-13'
    assert nbis['freshness']['earnings'] is None
    reversed_result=build_watch(base(),[m,r])
    assert reversed_result==result


def test_overlap_capacity_keeps_stage_and_parent_observations_separate():
    r=research();c=r['companies'][0]
    c['capacity']=[dict(id='power',status='operating',label='Site power',display='100 MW',value=100,unit='power_MW',definition='Utility power',scope='Project A',as_of='2026-09-30',source_ids=['s']),dict(id='IT',status='contracted',label='Site IT',display='80 MW',value=80,unit='IT_MW',definition='Contracted IT',scope='Project A',as_of='2026-09-30',source_ids=['s'])]
    c['relationships']=[{'company_id':'parent','relationship':'subsidiary','note':'Overlapping economic exposure'}]
    result=build_watch(base(),[r]);company=result['companies'][0]
    assert len(company['capacity'])==2 and 'capacity_total' not in company
    assert company['capacity_aggregation']['status']=='not_applicable'
    assert company['relationships']==c['relationships']


def test_future_equal_release_and_period_are_rejected():
    r=research();r['companies'][0]['quarters']=[dict(id='future',period_end='2027-01-01',release_date='2027-01-01',months=3,metrics={})]
    with pytest.raises(ValueError,match='Future'):build_watch(base(),[r])


def test_actual_reference_fixture_exercises_schema_drift_without_promotion():
    fixture=json.loads((ROOT/'tests/fixtures/earnings_reference.json').read_text())
    result=import_earnings_watch(fixture,source_commit=fixture['provenance']['commit'],source_path=fixture['provenance']['path'])
    assert len(result['candidates'])==4
    newest=next(c for c in result['candidates'] if c['ticker']=='CRWV' and c['release_date']=='2026-11-10')
    assert newest['company']=='CoreWeave'
    assert newest['alias_map']=={'rev_vs':'rev_vs_consensus','net_loss':'loss'}
    assert newest['candidate_fields']['rev']=='$3.661B (+168% YoY, +$1.0B q/q)'
    assert newest['period_end'] is None and newest['period_status']=='not_established'
    assert newest['market_reaction']['T+3_imported']=='+15.6%'
    assert newest['market_reaction']['T+1']['value'] is None
    assert result['metadata']['source_commit']=='51b2ca7cc767fddef3ff732dd9929528631aab63'
    assert all(row['status']=='pending_review' for row in result['candidates'])
    assert stage_changes(result,result,'2026-11-16')['changes']==[]


def test_reviewed_release_covers_nine_and_preserves_original_finance():
    from scripts.build_neocloud_watch import load_snapshot
    snapshot=load_snapshot()
    by_ticker={c['ticker']:c for c in snapshot['companies']}
    assert len(by_ticker)==19
    assert set(snapshot['focus_tickers'])==set(FOCUS)
    for ticker in FOCUS:
        c=by_ticker[ticker]
        assert c['quarters'] and c['latest_report_status']!='not_researched'
        latest=c['quarters'][0]
        assert latest['metrics']['revenue']['value'] is not None
        assert latest['metrics']['revenue']['source_ids']
        assert latest['months']==3 and latest['period_type']=='quarter'
        assert latest['metrics']['operating_cash_flow']['value'] is None or latest['metrics']['operating_cash_flow']['months']==3
    assert by_ticker['WYFI']['quarters'][0]['period_end']=='2026-09-30'
    assert by_ticker['HUT']['quarters'][0]['metrics']['revenue']['value']==71071000
    assert by_ticker['AGPU']['next_event']['date']=='2026-11-17'
    for original in base()['companies']:
        assert by_ticker[original['ticker']]['financing']==original
    assert len(snapshot['financing_rates'])>len(base()['financing_rates'])
    assert snapshot['import_audit']['source_commit']=='51b2ca7cc767fddef3ff732dd9929528631aab63'
    assert 'aethir_bridge' not in snapshot or isinstance(snapshot.get('aethir_bridge'),type(None))


def test_derivations_do_not_erase_cash_scope_or_fiscal_calendars():
    from scripts.build_neocloud_watch import load_snapshot
    snapshot=load_snapshot();companies={c['ticker']:c for c in snapshot['companies']}
    assert companies['IREN']['financing']['v2']['maturity_schedule']['period_basis']=='fiscal'
    assert companies['HUT']['financing']['v2']['maturity_schedule']['timing_issue']
    for c in snapshot['companies']:
        for q in c['quarters']:
            for f in q['metrics'].values():
                if f.get('status')=='derived':
                    assert f.get('input_ids') and f.get('formula')
                    assert f.get('source_ids') or f.get('value') is None
    agpu=companies['AGPU']['financing']
    assert agpu['metrics']['debt']['value']==413611
    assert agpu['v2']['market_cap']['ratio_blocker']
    assert agpu['v2']['debt_market_cap_percent'] is None
    assert companies['WYFI']['financing']['v2']['debt_market_cap_percent'] is not None
    assert companies['WYFI']['financing']['debt_context']['leases'][0]['value']==69252000
    assert companies['WYFI']['financing']['liquidity']['excluded_balances'][0]['value']==9012000
    assert 'prepayment' in (companies['AGPU']['financing_snapshot'].get('note','').lower()+str(companies['AGPU'].get('gaps','')).lower())



def test_release_document_fingerprint_stages_changed_source_without_promotion():
    from neocloud.watch import evidence_candidate
    original=evidence_candidate('https://issuer.example/q3-release','<html>Original document</html>')
    same=evidence_candidate('https://issuer.example/q3-release','<html>Original document</html>')
    changed=evidence_candidate('https://issuer.example/q3-release','<html>Corrected document</html>')
    assert stage_changes(original,same,'2026-11-16')['changes']==[]
    diffs=stage_changes(original,changed,'2026-11-16')['changes']
    assert len(diffs)==1 and diffs[0]['kind']=='changed'
    assert diffs[0]['new']['status']=='pending_review'
    assert 'value' not in diffs[0]['new']


def test_period_difference_rejects_reversed_inputs_even_when_amount_reconciles():
    from scripts.build_neocloud_watch import load_snapshot
    files=[json.loads(p.read_text()) for p in sorted((ROOT/'neocloud/data').glob('watch_*.json')) if p.name!='watch_import_audit.json']
    changed=deepcopy(files)
    hut=next(c for payload in changed for c in payload.get('companies',[]) if c['ticker']=='HUT' and 'quarters' in c)
    fact=hut['quarters'][0]['metrics']['operating_cash_flow']
    fact['calculation_inputs'].reverse()
    fact['value']=-fact['value']
    with pytest.raises(ValueError,match='compatible inputs'):
        build_watch(base(),changed)


def test_analyst_reads_are_short_sourced_and_do_not_mislabel_release_as_call():
    r=research()
    q=dict(id='crwv-q3',period_end='2026-09-30',release_date='2026-11-10',fiscal_label='Q3 2026',months=3,metrics={},
           analyst_read={'basis':'release_filing','reviewed_at':'2026-11-17','bullets':[{'label':'What matters','text':'An interpretation of the issuer filing.','source_ids':['s']}]})
    r['companies'][0]['quarters']=[q]
    build_watch(base(),[r])
    for bullets in [[],q['analyst_read']['bullets']*4]:
        changed=deepcopy(r);changed['companies'][0]['quarters'][0]['analyst_read']['bullets']=bullets
        with pytest.raises(ValueError,match='one to three'):build_watch(base(),[changed])
    changed=deepcopy(r);changed['companies'][0]['quarters'][0]['analyst_read'].update(basis='call_transcript',call_date='2026-11-10')
    with pytest.raises(ValueError,match='same company and quarter'):build_watch(base(),[changed])
    changed['sources'][0].update(source_kind='earnings_call_transcript',company_id='crwv',quarter_id='crwv-q3',call_date='2026-11-10')
    build_watch(base(),[changed])
    changed['sources'][0]['quarter_id']='crwv-q2'
    with pytest.raises(ValueError,match='same company and quarter'):build_watch(base(),[changed])


def test_actual_call_coverage_keeps_review_and_financial_dates_separate():
    from scripts.build_neocloud_watch import load_snapshot
    data=load_snapshot();focus=[c for c in data['companies'] if c['ticker'] in FOCUS]
    assert len(focus)==9
    for c in focus:
        read=c['quarters'][0]['analyst_read']
        assert read['basis']=='call_transcript' and 1<=len(read['bullets'])<=3
        assert read['reviewed_at']=='2026-11-17'
        for q in c['quarters'][1:]:assert q['analyst_read']['basis']=='release_filing'
    agpu=next(c for c in focus if c['ticker']=='AGPU')['quarters'][0]
    assert agpu['release_date']=='2026-08-14' and agpu['analyst_read']['call_date']=='2026-08-17'
    assert next(c for c in focus if c['ticker']=='SHAZ')['quarters'][0]['period_end']=='2026-06-30'
    assert data['reviewed_at']=='2026-11-16' # transcript review is not a fresh financial report
