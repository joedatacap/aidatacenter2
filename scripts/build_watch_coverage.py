"""Rebuild the evidence coverage matrix from the same validated website snapshot."""
from pathlib import Path
from build_neocloud_watch import load_snapshot
ROOT=Path(__file__).resolve().parents[1]
def generate():
 d=load_snapshot();rows=[]
 lines=['# Neocloud Watch V2 — coverage matrix','',f"Execution cutoff: {d['cutoff_at']}. Financial observations retain their individual dates. Software completion is separate from research completeness.",'','## Nine-company release','', '| Company / research group | Verified periods | Latest report review | Balance sheet | Operating evidence | Next catalyst |', '| --- | --- | --- | --- | --- | --- |']
 for c in d['companies']:
  if c['ticker'] not in d['focus_tickers']:continue
  quarters=[q for q in c['quarters'] if q['months']==3]
  periods=', '.join(q['period_end'] for q in quarters) or 'No comparable quarters'
  event=c.get('next_event')
  next_event=(event['date']+' · '+(event.get('label') or event.get('title') or 'Upcoming event')) if event else 'No confirmed future date'
  f=c.get('financing') or {};ops=c.get('operating_evidence_status') or ('Reviewed selected facts; partial' if c['capacity'] or c['contracts'] else 'Explicit coverage gap')
  lines.append('| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in [f"{c['ticker']} / {c['focus_group']}",periods,c['latest_report_status'],f.get('as_of','Not established'),ops,next_event])+' |')
 lines+=['','## Field and evidence limits','']
 sources={s['id']:s for s in d['sources']}
 for c in d['companies']:
  if c['ticker'] not in d['focus_tickers']:continue
  lines += [f"### {c['name']} ({c['ticker']})",'',c['latest_report_note'],'']
  for q in c['quarters']:
   reviewed=[k for k,v in q['metrics'].items() if v.get('value') is not None]
   absent=[k for k,v in q['metrics'].items() if v.get('value') is None]
   lines += [f"- {q['fiscal_label']} ended {q['period_end']} ({q['months']} months), released {q['release_date']}: reviewed {', '.join(reviewed) or 'none'}; missing/qualified {', '.join(absent) or 'none'}."]
  for gap in c['gaps']:
   lines.append('- Gap: '+(gap if isinstance(gap,str) else gap.get('reason',gap.get('note',str(gap)))))
  ids=list(dict.fromkeys(c.get('source_ids',[])+[s for q in c['quarters'] for s in q.get('source_ids',[])]))
  for id in ids:
   s=sources[id];lines.append(f"- [{s['title']}]({s['url']}) — published {s['published_at']}, retrieved {s['retrieved_at']}.")
  lines.append('')
 lines+=['## Common research gaps and market policy','', 'No verified original pre-release consensus series or dated split-adjusted T+1/T+5 price windows are loaded. T+3 import fields remain separate candidates. Guidance comparison is calculated only for matching metric, accounting basis, entity and future period. Missing is never zero. Operating IT load, utility power, GPU count, contracted ARR, contract face value and revenue are not aggregated.','',d['market_data_policy'],'','Market sources were re-read on November 16; their displayed observations remain November 13. Provider capitalization is rounded, date-only, and not independently reconciled across share classes. Nebius, SharonAI and Axe ratios remain qualified/withheld. Automated public market-data distribution terms are unresolved; no recurring quote feed is enabled.','', 'Refresh this matrix with `python3 scripts/build_watch_coverage.py` after reviewing and validating new research; this command never promotes candidate facts.','']
 return '\n'.join(lines)
if __name__=='__main__':
 target=ROOT/'docs/NEOCLOUD_WATCH_COVERAGE.md';target.write_text(generate());print(target)
