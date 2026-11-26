from copy import deepcopy
from scripts.equity_events import build_events

REPORTS=[{'id':'crwv','rating':'Hold','gaps':[{'input':'Verify cash receipts','source':'https://www.sec.gov'}]}]
def queue():
    return {'checked_at':'2026-11-26T10:00:00Z','status':'complete','sources':[{'id':'CRWV:sec','status':'ok'}],
            'items':[{'id':'test','ticker':'CRWV','url':'https://www.sec.gov/Archives/edgar/data/1769628/000176962826000461/report.htm',
                      'title':'Credit financing announcement','form':'8-K','published':'2026-11-25','status':'new'}]}


def test_accession_dedupes_documents_but_retains_each_and_review_questions():
    q=queue();q['items'].append({**q['items'][0],'url':q['items'][0]['url'].replace('report.htm','exhibit.htm'),'title':'Delivery acceptance'})
    result=build_events(q,REPORTS);row=result['events'][0]
    assert len(result['events'])==1
    assert len(row['documents'])==2
    assert row['categories']==['financing','delivery']
    assert row['impact']=='unassessed'
    assert row['open_report_gaps']==REPORTS[0]['gaps']
    assert result['summary']['no_changes_confirmed'] is False


def test_repeated_run_preserves_first_seen_review_and_no_duplicate_revision():
    q=queue();first=build_events(q,REPORTS);first['events'][0]['review']={'disposition':'dismissed','reason':'Already assessed'}
    q['checked_at']='2026-11-27T10:00:00Z';second=build_events(q,REPORTS,first)
    row=second['events'][0]
    assert row['first_seen']==first['checked_at']
    assert len(row['revisions'])==1
    assert row['status']=='dismissed'
    reports=deepcopy(REPORTS);reports[0]['rating']='Sell'
    assert len(build_events(q,reports,second)['events'][0]['revisions'])==2


def test_failure_keeps_history_and_never_reports_clear():
    prior=build_events(queue(),REPORTS)
    q=queue();q.update(status='failed',items=[],sources=[{'id':'CRWV:sec','status':'error','error':'timeout'}])
    result=build_events(q,REPORTS,prior)
    assert result['status']=='partial'
    assert len(result['events'])==1
    assert not result['events'][0]['seen_this_run']
    assert result['coverage']['source_errors']


def test_invalid_urls_dates_coverage_are_visible_errors():
    q=queue();q['items'][0]['url']='https://attacker.example/file';result=build_events(q,REPORTS)
    assert result['status']=='partial' and result['coverage']['errors']
    q=queue();q['items'][0]['published']='2027-01-01'
    assert build_events(q,REPORTS)['coverage']['errors']
    q=queue();q['sources']=[]
    assert build_events(q,REPORTS)['status']=='partial'


def test_nine_issuer_scan_includes_foreign_forms_and_presentation_links():
    import json
    from urllib.parse import urlsplit
    from scripts.equity_events import scan_equity, EXTRA_ISSUERS, PRESENTATIONS
    from scripts import check_terminal_disclosures as intake
    issuers={**intake.ISSUERS,**EXTRA_ISSUERS}
    original=dict(intake.ISSUERS)
    def fetch(url):
        if 'data.sec.gov' in url:
            cik=int(url.split('CIK')[1].split('.')[0]); ticker=next(k for k,v in issuers.items() if v['cik']==cik)
            return json.dumps({'cik':cik,'filings':{'recent':{'accessionNumber':[f'{cik:010d}-26-000001'],
                'form':['6-K' if ticker=='NBIS' else '20-F' if ticker=='IREN' else '8-K'],
                'filingDate':['2026-11-25'],'reportDate':['2026-09-30'],'primaryDocument':['results.htm']}}})
        config=next((v for v in issuers.values() if v['ir']==url),None)
        path=(config['path'].rstrip('/')+'/earnings-q3') if config else '/earnings.pdf'
        return '<a href="https://'+urlsplit(url).hostname+path+'">Quarterly earnings presentation</a>'
    queue=scan_equity(fetch=fetch,checked_at='2026-11-26T10:00:00Z')
    assert len(queue['sources'])==24
    assert {s['ticker'] for s in queue['sources']}==set(issuers)
    assert {'6-K','20-F','8-K'} <= {i['form'] for i in queue['items'] if i['form']}
    assert intake.ISSUERS==original
    assert queue['status']=='complete'
