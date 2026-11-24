"""One-off release evidence, limited to primary filing metadata."""
import json, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from pathlib import Path

results = []
for symbol, cik in {'CRWV':1769628,'NBIS':1513845,'IREN':1878848,'APLD':1144879,'HUT':1964789,'WULF':1083301,'WYFI':2042022,'SHAZ':2068385,'AGPU':1446159}.items():
    endpoint = f'https://data.sec.gov/submissions/CIK{cik:010d}.json'
    row = {'ticker':symbol,'url':endpoint,'checked_at':datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(endpoint,headers={'User-Agent':'Neocloud Watch research contact research@datacap.xyz'}),timeout=10) as res:
            doc = json.load(res)
        recent = doc['filings']['recent']
        row['issuer'] = doc['name']
        row['latest'] = recent['filingDate'][0]
        row['filings'] = [{k:recent[k][i] for k in ('accessionNumber','acceptanceDateTime','filingDate','form','primaryDocument','primaryDocDescription','items')} for i,date in enumerate(recent['filingDate']) if '2026-11-23'<=date<='2026-11-24']
    except (OSError, KeyError, ValueError) as exc:
        row['error'] = str(exc)
    results.append(row)
    time.sleep(.6)
Path('sec-index-result.json').write_text(json.dumps(results,indent=2))
