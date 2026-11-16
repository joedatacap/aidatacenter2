"""Bounded manual dry-run change detection. Never promotes facts or schedules jobs.

Use a local downloaded release snapshot or --url for a single public HTTPS JSON
source. Network failures are explicit; existing reviewed output remains usable.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from urllib.request import Request,urlopen
from neocloud.watch import import_earnings_watch,stage_changes,safe_url,evidence_candidate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input',type=Path);group.add_argument('--url');group.add_argument('--evidence-url',help='Single public issuer HTML/XML/filing document; fingerprint only, never automatic extraction.')
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--output',type=Path,default=Path('work/watch-refresh-candidates.json'))
    parser.add_argument('--cutoff',default=datetime.now(timezone.utc).date().isoformat())
    parser.add_argument('--dry-run',action='store_true',help='All executions are dry-run; included for explicit runbooks.')
    args=parser.parse_args()
    try:
        if args.input:payload=json.loads(args.input.read_text())
        else:
            source_url=args.evidence_url or args.url
            if not safe_url(source_url) or not source_url.startswith('https://'):raise ValueError('Public HTTPS URL without credentials required')
            with urlopen(Request(source_url,headers={'User-Agent':'NeocloudWatchResearch/2.0'}),timeout=20) as response:
                raw=response.read(5_000_001)
                if len(raw)>5_000_000:raise ValueError('Source exceeds bounded 5 MB snapshot limit')
                payload=evidence_candidate(source_url,raw) if args.evidence_url else json.loads(raw)
        candidate=payload if 'candidates' in payload else import_earnings_watch(payload,source_path=str(args.input) if args.input else args.url)
        baseline=json.loads(args.baseline.read_text()) if args.baseline else {'candidates':[]}
        baseline=baseline.get('candidate_snapshot',baseline)
        result=stage_changes(baseline,candidate,args.cutoff)
        result['candidate_snapshot']=candidate
    except Exception as exc:
        # No request headers, connection strings or environment values are logged.
        result={'mode':'dry_run','status':'source_access_limited','error_type':type(exc).__name__,
                'note':'Source could not be staged. Reviewed website data was not changed.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'mode':'dry_run','status':result.get('status','pending_review'),'changes':len(result.get('changes',[]))}))

if __name__=='__main__':main()
