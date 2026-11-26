from copy import deepcopy
from datetime import date
import json
import pytest
from scripts.equity_history import (snapshot_reports, snapshot_investment_reports, register_release,
    read_versions, build_scorecard, expected_session, target_date)


def archive(tmp_path):
    reports = tmp_path/'reports'; reports.mkdir()
    (reports/'cohort.json').write_text(json.dumps({'rows':[{'id':'abc'},{'id':'peer'}]}))
    (reports/'abc.json').write_text(json.dumps({'id':'abc','rating':'Hold','thesis':'Test'}))
    history=tmp_path/'history'
    version=snapshot_reports(reports,history,'2026-01-05T12:00:00Z')[0]
    register_release(history,version['version_id'],'2026-01-05T13:00:00Z','https://example.org/report','2026-01-05T14:00:00Z')
    return reports, history, version


def observations():
    return {symbol:[{'date':day,'close':value,'source_url':'https://example.org/prices','retrieved_at':'2026-01-14T12:00:00Z',
                      'basis':'split_adjusted_close','currency':'USD'} for day,value in [('2026-01-06',100),('2026-01-13',end)]]
            for symbol,end in [('ABC',120),('PEER',110),('QQQ',105),('NVDA',130)]}


def test_append_only_and_same_content_idempotency(tmp_path):
    reports, history, version=archive(tmp_path)
    assert snapshot_reports(reports,history,'2026-01-07T12:00:00Z')[0]==version
    p=reports/'abc.json'; x=json.loads(p.read_text()); x['rating']='Sell';p.write_text(json.dumps(x))
    snapshot_reports(reports,history,'2026-01-07T12:00:00Z')
    assert len(read_versions(history))==2
    with pytest.raises(ValueError): register_release(history,version['version_id'],'2026-01-06T13:00:00Z','https://example.org/report','2026-01-07T14:00:00Z')


def test_scoring_exact_sessions_and_frozen_cohort(tmp_path):
    _,history,_=archive(tmp_path)
    row=build_scorecard(history,observations(),'2026-01-14T13:00:00Z')['versions'][0]
    score=row['horizons']['1w']
    assert score['stock_return_pct']==20
    assert score['benchmarks']['QQQ']['excess_return_pp']==15
    assert score['benchmarks']['NVDA']['excess_return_pp']==-10
    assert score['benchmarks']['cohort']['return_pct']==10
    assert row['horizons']['1m']['reason']=='Horizon not elapsed'


def test_missing_entry_cannot_silently_enter_later(tmp_path):
    _,history,_=archive(tmp_path); data=observations(); data['ABC'][0]['date']='2026-01-07'
    row=build_scorecard(history,data,'2026-01-14T13:00:00Z')['versions'][0]
    assert row['entry_date'] is None
    assert all(s['status']=='pending' for s in row['horizons'].values())


def test_missing_exit_delisting_and_missing_peer_not_survivor_filtered(tmp_path):
    _,history,_=archive(tmp_path); data=observations(); data['PEER']=[]
    score=build_scorecard(history,data,'2026-01-14T13:00:00Z')['versions'][0]['horizons']['1w']
    assert score['benchmarks']['cohort']['missing_members']==['PEER']
    data['ABC'][1]['date']='2026-01-14'
    assert build_scorecard(history,data,'2026-01-14T13:00:00Z')['versions'][0]['horizons']['1w']['status']=='pending'


@pytest.mark.parametrize('field,value',[('close',True),('close',0),('close',float('nan')),('date','2027-01-01'),('retrieved_at','2027-01-01T00:00:00Z'),('source_url','http://example.org'),('currency','EUR')])
def test_invalid_observations(tmp_path,field,value):
    _,history,_=archive(tmp_path); data=observations();data['ABC'][0][field]=value
    with pytest.raises(ValueError): build_scorecard(history,data,'2026-01-14T13:00:00Z')


def test_preview_is_not_publication_and_raw_quotes_are_not_adjusted(tmp_path):
    _,history,_=archive(tmp_path); directory=tmp_path/'equity';directory.mkdir()
    (directory/'abc.json').write_text(json.dumps({'ticker':'ABC','as_of':'2025-12-01','report':{'rating':'Buy'},'sources':{}}))
    snapshot_investment_reports(directory,history,['abc','peer'],'2026-01-05T12:00:00Z')
    rows=build_scorecard(history,observations(),'2026-01-14T13:00:00Z')['versions']
    preview=next(r for r in rows if r['rating']=='Buy')
    assert preview['publication_status']=='publication_pending'
    assert preview['entry_date'] is None
    data=observations();data['ABC'][0]['basis']='raw_close'
    assert next(r for r in build_scorecard(history,data,'2026-01-14T13:00:00Z')['versions'] if r['rating']=='Hold')['horizons']['1w']['status']=='pending'


def test_calendar_and_month_end():
    assert expected_session(date(2026,11,26))==date(2026,11,27)
    assert expected_session(date(2026,4,3))==date(2026,4,6)
    assert target_date(date(2026,1,31),1,0)==date(2026,2,28)


def test_tampering_and_conflicting_observations_rejected(tmp_path):
    _,history,_=archive(tmp_path);data=observations();data['ABC'].append({**data['ABC'][0],'close':50})
    with pytest.raises(ValueError):build_scorecard(history,data,'2026-01-14T13:00:00Z')
    path=next((history/'versions').glob('*/*.json'));row=json.loads(path.read_text());row['content']['report']['rating']='Buy';path.write_text(json.dumps(row))
    with pytest.raises(ValueError):read_versions(history)
