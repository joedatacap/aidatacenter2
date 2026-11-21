"""Normalize a local reference snapshot into pending evidence candidates.

Only whitelisted earnings records are retained. No private multipurpose repo
sections or aggregate verdicts enter this adapter's output.
"""
import argparse
import json
from pathlib import Path
from neocloud.watch import import_earnings_watch

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path,default=Path('work/watch-import-candidates.json'))
    parser.add_argument('--source-commit',default='51b2ca7cc767fddef3ff732dd9929528631aab63')
    parser.add_argument('--source-path',default='password/neocloud/data.json')
    args=parser.parse_args()
    result=import_earnings_watch(json.loads(args.input.read_text()),source_commit=args.source_commit,source_path=args.source_path)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'pending_candidates':len(result['candidates']),'published_facts':0}))
