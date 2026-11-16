"""Reviewed Neocloud Watch snapshot, conservative imports and auditable comparisons.

This module never changes the historical directory and never promotes imported
free text into a verified financial fact. Static publishing uses reviewed JSON.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from urllib.parse import urlparse
from .website_v2 import debt_market_cap

FOCUS = {'CRWV':'benchmark','NBIS':'benchmark','IREN':'benchmark',
         'APLD':'medium','HUT':'medium','WULF':'medium',
         'WYFI':'smaller','SHAZ':'smaller','AGPU':'smaller'}
NAMES = {'CRWV':'CoreWeave','NBIS':'Nebius','IREN':'IREN','APLD':'Applied Digital',
         'HUT':'Hut 8','WULF':'TeraWulf','WYFI':'WhiteFiber','SHAZ':'SharonAI Holdings','AGPU':'Axe Compute'}
MISSING = {'not_disclosed','not_researched','not_applicable','conflicting','stale','unknown','unavailable','insufficient_evidence'}
METRICS = ('revenue','operating_income','operating_margin','adjusted_ebitda','operating_cash_flow','cash_capex','revenue_yoy','revenue_qoq')


def missing(reason='No reviewed observation loaded.', status='not_researched'):
    return {'value':None,'status':status,'reason':reason}


def finite(value):
    if isinstance(value,bool):
        raise ValueError('Boolean cannot be a financial value')
    try:
        n=Decimal(str(value))
    except (InvalidOperation,TypeError) as exc:
        raise ValueError('Invalid financial value') from exc
    if not n.is_finite():
        raise ValueError('Non-finite financial value')
    return n


def iso(value):
    return date.fromisoformat(str(value)[:10])


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def safe_url(value):
    parsed=urlparse(str(value))
    return parsed.scheme in {'http','https'} and bool(parsed.netloc) and not parsed.username and not parsed.password


def market_cap_band(value):
    if value is None:return 'unknown'
    n=finite(value)
    if n<0:raise ValueError('Market capitalization cannot be negative')
    return 'large' if n>=10_000_000_000 else 'mid' if n>=2_000_000_000 else 'small' if n>=300_000_000 else 'micro'


def comparable(a,b):
    """Inputs are like-for-like only when their entity, period-length and basis agree."""
    return all(a.get(k)==b.get(k) and a.get(k) is not None for k in ('scope','currency','unit','months','accounting_basis'))


def percentage_change(current, previous, *, formula='percentage_change/v1'):
    if current.get('value') is None or previous.get('value') is None:
        return missing('One or both source observations are missing.')
    if not comparable(current,previous):
        return missing('Metric scope, currency, period length or accounting basis differs.','not_applicable')
    old,new=finite(previous['value']),finite(current['value'])
    if old<=0:
        return {'value':None,'status':'not_applicable','reason':'N/M: comparison base is zero or negative.',
                'absolute_change':float(new-old),'input_ids':[previous['id'],current['id']], 'formula':formula}
    return {'value':float(((new-old)/old*100).quantize(Decimal('.01'))),'status':'derived','unit':'percent',
            'definition':'Like-for-like percentage change','scope':current['scope'],'currency':current['currency'],
            'months':current['months'],'accounting_basis':current['accounting_basis'],
            'source_ids':list(dict.fromkeys(previous.get('source_ids',[])+current.get('source_ids',[]))),
            'input_ids':[previous['id'],current['id']],'formula':formula}


def quarter_from_ytd(current,previous):
    """Quarter cash flow requires compatible cumulative periods in one fiscal year."""
    if any(x.get('value') is None for x in (current,previous)):
        return missing('Both cumulative inputs are required.')
    keys=('fiscal_year','fiscal_year_start','scope','currency','unit','accounting_basis','metric')
    if not all(current.get(k) is not None and current.get(k)==previous.get(k) for k in keys):
        raise ValueError('YTD inputs must share fiscal year, scope, currency and basis')
    if current.get('period_type')!='ytd' or previous.get('period_type')!='ytd' or current.get('months',0)-previous.get('months',0)!=3:
        raise ValueError('Quarter derivation requires adjacent compatible YTD observations')
    if iso(current['period_end'])<=iso(previous['period_end']):raise ValueError('YTD dates out of order')
    out=deepcopy(current)
    out.update(value=float(finite(current['value'])-finite(previous['value'])),status='derived',months=3,period_type='quarter',
               formula='quarter_from_ytd/v1',input_ids=[previous['id'],current['id']],
               source_ids=list(dict.fromkeys(previous.get('source_ids',[])+current.get('source_ids',[]))))
    return out


def guidance_change(old,new):
    keys=('metric','currency','unit','scope','accounting_basis','period_end','period_start')
    if not all(old.get(k) is not None and old.get(k)==new.get(k) for k in keys):
        return {'classification':'not_comparable','reason':'Guidance metric, future period, scope or accounting basis differs.'}
    if iso(old['as_of'])>=iso(new['as_of']):raise ValueError('Guidance chronology must preserve original before revision')
    if any(x.get(k) is None for x in (old,new) for k in ('low','high')):
        return {'classification':'insufficient_evidence','reason':'A prior or current guidance range is missing.'}
    for x in (old,new):
        if finite(x['low'])>finite(x['high']):raise ValueError('Reversed guidance range')
    previous=(finite(old['low'])+finite(old['high']))/2
    current=(finite(new['low'])+finite(new['high']))/2
    delta=current-previous
    return {'classification':'raised' if delta>0 else 'cut' if delta<0 else 'maintained',
            'old_midpoint':float(previous),'new_midpoint':float(current),'absolute_change':float(delta),
            'percent_change':float(delta/previous*100) if previous>0 else None,
            'percent_reason':None if previous>0 else 'N/M: non-positive prior midpoint',
            'formula':'guidance_midpoint/v1','input_ids':[old['id'],new['id']]}


def consensus_surprise(actual,estimate,release_at):
    if not estimate or estimate.get('value') is None:return missing('Pre-release consensus unavailable.','not_researched')
    observed=datetime.fromisoformat(estimate['observed_at'].replace('Z','+00:00'))
    released=datetime.fromisoformat(release_at.replace('Z','+00:00'))
    if observed.tzinfo is None or released.tzinfo is None:raise ValueError('Consensus timing requires explicit timezones')
    if observed>=released:raise ValueError('Post-release estimate cannot establish a historical surprise')
    for key in ('metric','accounting_basis','scope','currency','unit','period_end','months'):
        if actual.get(key) is None or actual.get(key)!=estimate.get(key):return missing('Actual and estimate are not comparable.','not_applicable')
    if finite(estimate['value'])<=0:return missing('N/M: estimate denominator is non-positive.','not_applicable')
    return {'value':float((finite(actual['value'])/finite(estimate['value'])-1)*100),'status':'derived',
            'unit':'percent','formula':'consensus_surprise/v1','input_ids':[estimate['id'],actual['id']],
            'definition':'Actual relative to comparable pre-release consensus','scope':actual['scope'],
            'source_ids':list(dict.fromkeys(estimate.get('source_ids',[])+actual.get('source_ids',[])))}


def market_reaction(before,after, *, horizon,release_at,first_session,fifth_session,pre_release_session):
    if horizon not in ('T+1','T+5'):raise ValueError('Only requested T+1 and T+5 windows are supported')
    if not before or not after:return missing('Dated adjusted closing observations unavailable.')
    expected=first_session if horizon=='T+1' else fifth_session
    if after.get('session')!=expected or before.get('session')!=pre_release_session:raise ValueError('Observation does not match the requested trading session')
    if not before.get('split_adjusted') or not after.get('split_adjusted'):raise ValueError('Split treatment must be explicit')
    if before.get('basis')!='price_return' or after.get('basis')!='price_return':raise ValueError('Price/total return bases differ')
    if before.get('currency')!=after.get('currency') or before.get('ticker')!=after.get('ticker'):raise ValueError('Market identity differs')
    released=datetime.fromisoformat(release_at.replace('Z','+00:00'))
    closed=datetime.fromisoformat(before['closed_at'].replace('Z','+00:00'))
    post_closed=datetime.fromisoformat(after['closed_at'].replace('Z','+00:00'))
    if released.tzinfo is None or closed.tzinfo is None or closed>=released:raise ValueError('Pre-release close is not before release')
    if post_closed.tzinfo is None or post_closed<=released:raise ValueError('Post-release close is not after release')
    if str(after['closed_at'])[:10]!=after['session'] or str(before['closed_at'])[:10]!=before['session']:raise ValueError('Close timestamps do not match their trading sessions')
    if finite(before['value'])<=0:raise ValueError('Invalid market denominator')
    return {'value':float((finite(after['value'])/finite(before['value'])-1)*100),'status':'derived',
            'unit':'percent','horizon':horizon,'basis':'split-adjusted price return','release_at':release_at,
            'formula':'event_close_return/v1','input_ids':[before['id'],after['id']],
            'definition':'Split-adjusted pre-release close to requested post-release session close',
            'scope':before['ticker'],'source_ids':list(dict.fromkeys(before.get('source_ids',[])+after.get('source_ids',[]))),
            'note':'Association around the reporting event does not establish causation.'}


# Explicit whitelist excludes private strategy sections, sentiment, verdicts,
# community posts, monitoring internals and account configuration.
IMPORT_FIELDS=('rev','eps','ebitda','loss','cash','capex','guidance','tcv','rev_vs_consensus',
               'drift_3d','sec_10q','ir_links','transcript_links','call_links','sources')


def import_earnings_watch(payload,registry=None, *, source_commit=None,source_path=None):
    registry=registry or {ticker:{'id':ticker.lower(),'name':name} for ticker,name in NAMES.items()}
    candidates={}
    rows=payload.get('earnings',{}).get('reported',payload.get('reported',payload.get('records',[])))
    if not isinstance(rows,list):rows=[]
    for raw in rows:
        ticker=str(raw.get('ticker','')).upper()
        if ticker not in registry:continue
        safe={key:deepcopy(raw[key]) for key in IMPORT_FIELDS if key in raw}
        alias_map={}
        if 'rev_vs' in raw and 'rev_vs_consensus' not in safe:
            safe['rev_vs_consensus']=raw['rev_vs'];alias_map['rev_vs']='rev_vs_consensus'
        if 'net_loss' in raw and 'loss' not in safe:
            safe['loss']=raw['net_loss'];alias_map['net_loss']='loss'
        period_end=raw.get('period_end')
        if period_end:
            try:iso(period_end)
            except ValueError:period_end=None
        content={'company_id':registry[ticker]['id'],'ticker':ticker,'company':registry[ticker]['name'],
                 'release_date':raw.get('date'),'period_end':period_end,'scope':raw.get('scope','unresolved'),
                 'revision':raw.get('revision','as_imported'),'candidate_fields':safe,
                 'alias_map':alias_map,'status':'pending_review',
                 'period_status':'provided_unverified' if period_end else 'not_established',
                 'source_commit':source_commit,'source_path':source_path,
                 'market_reaction':{'T+1':missing('Imported T+3 is not a T+1 observation.'),
                                    'T+5':missing('Imported T+3 is not a T+5 observation.'),
                                    'T+3_imported':raw.get('drift_3d')},
                 'reason':'Imported free text is a research candidate; primary evidence and fiscal-period review are required.'}
        # Identity is stable when an amount changes; content hash captures revisions.
        logical_key={key:content[key] for key in ('company_id','period_end','scope','revision')}
        if period_end is None:logical_key['release_date']=content['release_date']
        content['id']='candidate-'+digest(logical_key)[:20]
        content['content_digest']=digest(content)
        previous=candidates.get(content['id'])
        if previous and previous['content_digest']!=content['content_digest']:
            variants=previous.get('conflicting_candidates',[previous])+[content]
            variants=sorted({v['content_digest']:v for v in variants}.values(),key=lambda v:v['content_digest'])
            content=deepcopy(variants[0]);content['conflicting_candidates']=variants
            content['reason']='Conflicting imported records share a logical identity; manual source review required.'
        candidates[content['id']]=content
    updated=payload.get('updated')
    return {'schema_version':1,'metadata':{'raw_updated':updated,'raw_as_of':payload.get('as_of'),
            'raw_stale':payload.get('stale'),'timezone':'not_established' if updated and not re.search(r'(Z|[+-]\d\d:\d\d)$',str(updated)) else 'as_provided',
            'freshness_status':'unverified_per_record','source_commit':source_commit,'source_path':source_path},
            'candidates':sorted(candidates.values(),key=lambda x:x['id']),
            'excluded_sections':['aethir_bridge','basket','delta','community','verdicts','private_strategy'],
            'publication_policy':'Candidates are not published as reviewed financial observations.'}


def evidence_candidate(url,body):
    """Fingerprint a public release/filing for review; never extract verified facts."""
    if not safe_url(url):raise ValueError('Unsafe evidence source URL')
    if isinstance(body,str):body=body.encode()
    content_hash=hashlib.sha256(body).hexdigest()
    identity='evidence-'+hashlib.sha256(url.encode()).hexdigest()[:20]
    # No page scripts or narrative are promoted. A reviewer opens the source.
    return {'schema_version':1,'candidates':[{'id':identity,'status':'pending_review',
            'source_url':url,'content_sha256':content_hash,'size_bytes':len(body),
            'reason':'Source document added or changed; review issuer date, periods and evidence before updating published facts.'}],
            'publication_policy':'Document fingerprints detect candidate changes only; reviewed dataset unchanged.'}


def stage_changes(baseline,candidate,cutoff):
    """Stable dry-run candidate differences; no writes or automatic promotion."""
    before={x['id']:x for x in baseline.get('candidates',[])}
    after={x['id']:x for x in candidate.get('candidates',[])}
    changes=[]
    for key in sorted(set(before)|set(after)):
        a,b=before.get(key),after.get(key)
        if a!=b:changes.append({'id':key,'status':'pending_review','kind':'added' if a is None else 'removed' if b is None else 'changed','old':a,'new':b})
    expired=[]
    for event in candidate.get('events',[]):
        if event.get('date') and iso(event['date'])<iso(cutoff) and event.get('status') in ('confirmed','estimated','upcoming'):
            expired.append(dict(event,status='needs_reconciliation',reason='Event date is before the execution cutoff.'))
    return {'schema_version':1,'mode':'dry_run','cutoff':cutoff,'changes':changes,'expired_events':expired,
            'candidate_digest':digest(candidate),'promotion':'Manual evidence review required; published data unchanged.'}


def build_watch(directory,research_files, *, reviewed_at=None,import_audit=None,cutoff_at=None):
    """Merge reviewed research with an immutable copy of the existing finance ledger."""
    out=deepcopy(directory)
    cutoff=reviewed_at or max((r.get('reviewed_at','2026-11-16') for r in research_files),default='2026-11-16')
    iso(cutoff)
    cutoff_at=cutoff_at or max((p.get('cutoff_at',p.get('reviewed_cutoff_at','')) for p in research_files),default='') or '2026-11-16T05:22:15Z'
    observed_cutoff=datetime.fromisoformat(cutoff_at.replace('Z','+00:00'))
    if observed_cutoff.tzinfo is None:raise ValueError('Execution cutoff requires explicit timezone')
    sources={s['id']:deepcopy(s) for s in out['sources']}
    research={}
    for payload in research_files:
        for source in payload.get('sources',[]):
            if source['id'] in sources and source!=sources[source['id']]:raise ValueError('Conflicting source id')
            if not safe_url(source.get('url')):raise ValueError('Unsafe evidence URL')
            if not all(source.get(k) for k in ('title','excerpt','published_at','retrieved_at')):raise ValueError('Evidence requires dated supporting excerpt')
            iso(source['published_at']);iso(source['retrieved_at'])
            sources[source['id']]=deepcopy(source)
        for company in payload.get('companies',[]):
            ticker=company['ticker']
            if ticker in research:
                # Additive market-only snapshots do not overwrite quarterly history.
                market_only={'id','ticker','market_observation','market_cap','market_cap_note'}
                if set(company)-market_only and set(research[ticker])-market_only:
                    raise ValueError('Duplicate research company')
                research[ticker].update(deepcopy(company))
            else:research[ticker]=deepcopy(company)
    if not set(FOCUS).issubset(research):raise ValueError('All nine focus companies require explicit research status')

    def refs(record,required=True):
        ids=record.get('source_ids',[])
        if required and not ids:raise ValueError('Reviewed material fact requires source evidence')
        if any(s not in sources for s in ids):raise ValueError('Unresolved evidence source')

    def validate_fact(f,context=None):
        if not isinstance(f,dict):raise ValueError('Financial observation must be structured')
        if f.get('value') is None:
            if f.get('status') not in MISSING:raise ValueError('Missing number requires explicit missing status')
            if not (f.get('reason') or f.get('note')):raise ValueError('Missing number requires reason')
            refs(f,False);return
        finite(f['value']);refs(f)
        if not f.get('definition') or not f.get('scope') or not f.get('unit'):raise ValueError('Number needs definition, scope and unit')
        if f.get('status') in MISSING:raise ValueError('Missing-status fact cannot contain a numeric value')
        if f.get('as_of') and iso(f['as_of'])>iso(cutoff):raise ValueError('Future financial observation')
        if f.get('status')=='derived' and not (f.get('input_ids') and f.get('formula')):raise ValueError('Derived fact requires formula and input ids')
        if f.get('calculation_inputs'):
            for item in f['calculation_inputs']:
                finite(item['value']);refs(item)
            if f.get('formula') in ('period_difference/v1','period_difference_v1'):
                a,b=f['calculation_inputs']
                if a['months']-b['months']!=3 or any(a.get(k) is None or a.get(k)!=b.get(k) for k in ('scope','currency','unit','accounting_basis','fiscal_year')):
                    raise ValueError('Period difference requires compatible inputs')
                if iso(a['period_end']) != iso(f['period_end']) or not 70 <= (iso(a['period_end'])-iso(b['period_end'])).days <= 110:
                    raise ValueError('Period difference requires adjacent chronological period ends')
                if any(f.get(k)!=a.get(k) for k in ('scope','currency','unit','accounting_basis')):
                    raise ValueError('Derived period scope or basis differs from inputs')
                if finite(a['value'])-finite(b['value'])!=finite(f['value']):raise ValueError('Derived period difference does not reconcile')

    original={c['ticker']:c for c in out['companies']}
    companies=[]
    financing_rates=deepcopy(out.get('financing_rates',[]))
    rate_ids={r['id'] for r in financing_rates}
    for ticker in list(original)+[t for t in research if t not in original]:
        finance=deepcopy(original.get(ticker))
        c=research.get(ticker,{})
        company={'id':ticker.lower(),'ticker':ticker,'name':NAMES.get(ticker,finance.get('name') if finance else ticker),
                 'aliases':[ticker],'focus_group':FOCUS.get(ticker,'context'),
                 'business_model':finance.get('group','other') if finance else 'other',
                 'latest_report_status':'not_researched','latest_report_note':'Retained contextual company; latest earnings review is outside the nine-name focus.',
                 'quarters':[],'guidance':[],'milestones':[],'capacity':[],'contracts':[],'hardware':[],'events':[],'gaps':[],**c}
        company['focus_group']=FOCUS.get(ticker,'context')
        company['financing']=finance
        if not re.fullmatch(r'[a-z0-9-]+',company['id']):raise ValueError('Unsafe stable company id')
        company['aliases']=list(dict.fromkeys([ticker]+company.get('aliases',[])))
        # Context peers retain their original reviewed operating records too.
        for category in ('capacity','contracts','hardware'):
            if not company.get(category) and finance:
                company[category]=deepcopy(finance.get('v2',{}).get(category,[]))
        for rate in company.get('financing_rates',[]):
            refs(rate)
            if rate['id'] in rate_ids:raise ValueError('Duplicate financing rate identity')
            if rate.get('ticker',ticker)!=ticker:raise ValueError('Financing borrower identity differs')
            if rate.get('rate_percent') is not None:
                if finite(rate['rate_percent'])<0:raise ValueError('Negative contractual rate')
                if rate.get('kind')=='floating_formula' and not rate.get('benchmark_fixing'):
                    raise ValueError('Floating all-in rate requires dated benchmark fixing')
            rate['ticker']=ticker;financing_rates.append(deepcopy(rate));rate_ids.add(rate['id'])
        for instrument in company.get('debt_inventory',[]):
            refs(instrument)
            if finite(instrument['principal'])<0:raise ValueError('Negative principal')
            if instrument.get('as_of') and iso(instrument['as_of'])>iso(cutoff):raise ValueError('Future principal observation')
        for key in ('quarters','guidance','milestones','capacity','contracts','hardware','events','gaps'):
            company.setdefault(key,[])
        quarter_ids=set()
        for q in company['quarters']:
            if q['id'] in quarter_ids:raise ValueError('Duplicate quarter id')
            quarter_ids.add(q['id'])
            end=iso(q['period_end']);released=iso(q['release_date'])
            if end>iso(cutoff) or released>iso(cutoff):raise ValueError('Future earnings period or release')
            if released<end:raise ValueError('Release cannot precede reported period end')
            if q.get('months') not in (3,6,9,12):raise ValueError('Explicit quarter/YTD/annual period length required')
            q.setdefault('period_type','quarter' if q['months']==3 else 'annual' if q['months']==12 else 'ytd')
            if q['period_type']=='quarter' and q['months']!=3:raise ValueError('YTD cannot masquerade as a quarter')
            q.setdefault('scope','consolidated');q.setdefault('metrics',{})
            refs(q,False)
            for key,f in q['metrics'].items():
                f.setdefault('id',q['id']+'-'+key);f.setdefault('period_end',q['period_end']);f.setdefault('months',q['months'])
                f.setdefault('scope',q['scope']);f.setdefault('accounting_basis','issuer_adjusted' if key=='adjusted_ebitda' else 'GAAP')
                f.setdefault('published_at',q['release_date']);f.setdefault('source_ids',q.get('source_ids',[]))
                if f.get('value') is not None and not f.get('currency'):f['currency']='USD' if f.get('unit')=='USD' else 'not_applicable'
                validate_fact(f)
                f['retrieved_at']=max((sources[s].get('retrieved_at','') for s in f.get('source_ids',[])),default=None)
            for key in METRICS:q['metrics'].setdefault(key,missing('No reviewed '+key.replace('_',' ')+' observation for this period.'))
            q.setdefault('consensus',missing('No original pre-release consensus snapshot with comparable metric and timestamp.'))
            q.setdefault('market_reaction',{'T+1':missing('Dated split-adjusted event-window closes not established.'),'T+5':missing('Dated split-adjusted event-window closes not established.')})
        company['quarters'].sort(key=lambda q:(q['period_end'],q['release_date']),reverse=True)
        for q in company['quarters']:
            if q['months']!=3:continue
            current=q['metrics']['revenue']
            prior_revenue=q['metrics'].get('revenue_prior_year')
            if prior_revenue and prior_revenue.get('value') is not None and prior_revenue.get('period_end') and iso(prior_revenue['period_end']).year==iso(q['period_end']).year-1 and iso(prior_revenue['period_end']).month==iso(q['period_end']).month:
                q['metrics']['revenue_yoy']=percentage_change(current,prior_revenue,formula='revenue_yoy/v1')
            prior_year=[p for p in company['quarters'] if p['months']==3 and iso(p['period_end']).year==iso(q['period_end']).year-1 and iso(p['period_end']).month==iso(q['period_end']).month]
            prior_quarter=[p for p in company['quarters'] if p['months']==3 and 70<=(iso(q['period_end'])-iso(p['period_end'])).days<=110]
            for field,rows in [('revenue_yoy',prior_year),('revenue_qoq',prior_quarter)]:
                if q['metrics'][field].get('value') is None and rows:
                    result=percentage_change(current,rows[0]['metrics']['revenue'],formula=field+'/v1')
                    result['id']=q['id']+'-'+field;q['metrics'][field]=result
            revenue=q['metrics']['revenue'];operating=q['metrics']['operating_income']
            if q['metrics']['operating_margin'].get('value') is None and revenue.get('value') is not None and operating.get('value') is not None and comparable(revenue,operating) and finite(revenue['value'])>0:
                q['metrics']['operating_margin']={'id':q['id']+'-operating-margin','value':float(finite(operating['value'])/finite(revenue['value'])*100),'status':'derived','unit':'percent','definition':'GAAP operating income divided by recognized revenue','scope':q['scope'],'input_ids':[operating['id'],revenue['id']],'formula':'operating_margin/v1','source_ids':list(dict.fromkeys(operating.get('source_ids',[])+revenue.get('source_ids',[])))}
        for category in ('capacity','contracts','hardware','milestones','events','guidance'):
            for record in company[category]:
                refs(record,record.get('status') not in MISSING)
                if 'value' in record and record.get('value') is not None:validate_fact(record)
                # Deadlines may be future; observed facts may not.
                if record.get('as_of') and iso(record['as_of'])>iso(cutoff):raise ValueError('Future evidence observation')
                if category=='guidance' and record.get('previous') and record.get('current'):
                    for observation in (record['previous'],record['current']):
                        refs(observation)
                        if observation.get('low') is not None:finite(observation['low'])
                        if observation.get('high') is not None:finite(observation['high'])
                    record['change']=guidance_change(record['previous'],record['current'])
                if category=='milestones':
                    verdict=record.get('classification',record.get('status'))
                    if verdict in ('met','missed') and not record.get('outcome'):
                        raise ValueError('Delivery verdict requires an evidenced outcome')
                    original_target=record.get('original_target')
                    if original_target:
                        refs(original_target)
                        if original_target.get('as_of') and iso(original_target['as_of'])>iso(cutoff):raise ValueError('Future original target observation')
                    for observation in record.get('revisions',[])+([record['outcome']] if isinstance(record.get('outcome'),dict) else []):
                        refs(observation)
                        if observation.get('as_of') and iso(observation['as_of'])>iso(cutoff):raise ValueError('Future milestone observation')
                    if verdict in ('met','missed') and not original_target:
                        raise ValueError('Delivery verdict requires original target evidence')
        # New-company financing is separate from the original immutable ledger.
        snap=company.get('financing_snapshot')
        if snap:
            refs(snap)
            for key in ('debt','cash'):
                snap.setdefault(key,missing('Borrowing/cash definition not reconciled.'))
                if snap[key].get('value') is not None:
                    snap[key].setdefault('as_of',snap['as_of']);validate_fact(snap[key])
                    if finite(snap[key]['value'])<0:raise ValueError('Borrowing and cash balances cannot be negative')
            for excluded in snap.get('leases',[])+snap.get('excluded_balances',[]):
                refs(excluded)
                if finite(excluded['value'])<0:raise ValueError('Negative lease/excluded balance')
            if finance is None:
                finance={'ticker':ticker,'name':company['name'],'group':company['business_model'],'listing_status':'listed',
                         'as_of':snap['as_of'],'filed_at':snap.get('published_at',snap['as_of']),'scope':snap.get('scope','consolidated'),
                         'metrics':{'debt':deepcopy(snap['debt']),'cash':deepcopy(snap['cash'])},'notes':[snap.get('note','')],
                         'debt_context':{'leases':deepcopy(snap.get('leases',[])),'bridges':[],'notes':[]},
                         'liquidity':{'takeaway':snap.get('note',''),'cash_caveat':snap.get('note','Cash availability to parent not established.'),'facilities':[],'excluded_balances':deepcopy(snap.get('excluded_balances',[])),'notes':[]},
                         'v2':{'market_cap':None,'debt_market_cap_percent':None,'debt_inventory':company.get('debt_inventory',[]),'maturity_schedule':None,'contracts':company['contracts'],'capacity':company['capacity'],'hardware':company['hardware'],'revenue':[],'events':company['events']}}
                company['financing']=finance
        market=company.get('market_observation') or company.get('market_cap') or (finance or {}).get('v2',{}).get('market_cap')
        if market:
            if market.get('value') is not None:
                refs(market)
                if market.get('currency')!='USD' or finite(market['value'])<=0:raise ValueError('Market observation requires positive dated USD capitalization')
                if market.get('as_of') and iso(market['as_of'])>iso(cutoff):raise ValueError('Future market observation')
            company['market_cap']=deepcopy(market)
            if ticker not in original and finance:
                finance['v2']['market_cap']=deepcopy(market)
                finance['v2']['debt_market_cap_percent']=debt_market_cap(finance['metrics']['debt'].get('value'),market,listing=finance['listing_status'],debt_date=finance['as_of'])
        company['market_cap_band']=market_cap_band(market.get('value')) if market else 'unknown'
        company['freshness']={'earnings':company['quarters'][0]['period_end'] if company['quarters'] else None,
                              'balance_sheet':finance.get('as_of') if finance else None,
                              'operations':max((f.get('as_of','') for key in ('capacity','contracts','hardware') for f in company[key]),default=None),
                              'market_data':market.get('as_of') if market else None}
        company['capacity_aggregation']={'status':'not_applicable','reason':'Statuses, IT versus power units, project phases and ownership may overlap; rows are not summed.'}
        company['next_event']=next((e for e in sorted(company['events'],key=lambda e:e.get('date','9999')) if e.get('date') and iso(e['date'])>=iso(cutoff)),None)
        company['reconciliation_queue']=[dict(e,status='needs_reconciliation') for e in company['events'] if e.get('date') and iso(e['date'])<iso(cutoff) and e.get('status') in ('upcoming','confirmed','estimated')]
        companies.append(company)
    if len({c['id'] for c in companies})!=len(companies):raise ValueError('Duplicate stable company identity')
    return {'schema_version':1,'reviewed_at':cutoff,'cutoff_at':cutoff_at,'focus_tickers':list(FOCUS),'companies':companies,
            'sources':list(sources.values()),'financing_rates':financing_rates,
            'instruments':deepcopy(out.get('instruments',[])),
            'import_audit':import_audit or {'status':'reference_reviewed_separately','publication':'No imported candidates promoted automatically.'},
            'market_data_policy':'Manually reviewed dated provider snapshots; no licensed live feed or automatic redistribution claimed.',
            'corrections':[{'date':'2026-11-16','note':'Additive reviewed Watch snapshot; original directory and prior V2 observations preserved.'}]}
