"""Deterministic final dossiers preserve accepted evidence when inference is unavailable."""
from copy import deepcopy


def source_results(run):
    seen=set()
    for value in run.get('source_cache',{}).values():
        values=value if isinstance(value,list) else [value]
        for source in values:
            if not isinstance(source,dict) or not source.get('url') or source['url'] in seen:
                continue
            seen.add(source['url'])
            yield source


def meaningful_research(run):
    return bool(run.get('evidence') or run.get('instruments') or
                any(t['role']!='manager' and t['status']=='completed' for t in run['tasks']) or
                any(s.get('status')=='retrieved' for s in source_results(run)))


def complete_evidence(run):
    if run['mode']=='simulated':
        return bool(run.get('dossier'))
    if not any(t['role']=='auditor' and t['status']=='completed' for t in run['tasks']):
        return False
    evidence={e['id'] for e in run['evidence'] if e.get('provenance')=='live'}
    def ready(item):
        rate_known=item.get('coupon_pct') is not None if item.get('rate_type') in ('fixed','convertible') else bool(item.get('reference_index')) and item.get('spread_bps') is not None
        return (item.get('provenance')=='live' and item.get('verification_status')=='auditor_verified'
                and bool(set(item.get('evidence_ids',[]))&evidence)
                and all(item.get(field) is not None for field in ('issue_date','outstanding_principal','snapshot_date','maturity'))
                and rate_known)
    return all(any(i['ticker']==ticker and ready(i) for i in run['instruments']) for ticker in run['tickers'])


def build_dossier(run,outcome,reason):
    previous=run.get('dossier') or {}
    model_notes=previous.get('model_notes') or (previous.get('summary') if previous.get('generator') is None else None)
    verified=[deepcopy(i) for i in run['instruments'] if i.get('provenance')=='live' and i.get('verification_status')=='auditor_verified']
    provisional=[deepcopy(i) for i in run['instruments'] if i not in verified]
    concerns=[]
    for ticker in run['tickers']:
        if not any(i['ticker']==ticker for i in verified):
            concerns.append(ticker+': no auditor-verified live instrument; outstanding debt remains unknown.')
    for item in run['instruments']:
        missing=[name for name in ('issue_date','outstanding_principal','snapshot_date','maturity') if item.get(name) is None]
        if missing:
            concerns.append(item['instrument_id']+': unknown '+', '.join(missing)+'.')
        if item.get('rate_type')=='floating' and item.get('hedge_status')=='unknown':
            concerns.append(item['instrument_id']+': hedge exposure unverified; not assumed unhedged.')
    unavailable=[]
    for source in source_results(run):
        if source.get('status') not in ('retrieved','fixture'):
            unavailable.append({'url':source['url'],'category':source.get('category','unavailable'),
                                'http_status':source.get('http_status')})
    for item in run['tasks']:
        if item['status']=='failed':
            concerns.append(item['role']+' task exhausted retries: '+item['id'])
    concerns.extend(str(c)[:1000] for c in previous.get('concerns',[]) if isinstance(c,str))
    if unavailable:
        concerns.append(str(len(unavailable))+' primary source URLs unavailable; these are access failures, not evidence of no debt.')
    if not run.get('market_observations'):
        concerns.append('Market data unavailable. No prices, yields or returns fabricated.')
    prefix='SIMULATED — ' if run['mode']=='simulated' else ''
    summary=prefix+outcome.replace('_',' ').capitalize()+'. '+str(len(verified))+' auditor-verified live instrument records; '+str(len(provisional))+' provisional or fixture records. '+reason
    return {'summary':summary,'outcome':outcome,'generator':'evidence_snapshot',
            'model_notes':model_notes,'verified_information':verified,'provisional_information':provisional,
            'concerns':list(dict.fromkeys(concerns)),'source_failures':unavailable,
            'evidence_ids':[e['id'] for e in run['evidence']],
            'completion_note':'Missing financial amounts remain unknown; no totals inferred from incomplete coverage.'}
