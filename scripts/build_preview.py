"""Export credential-free demo cases using the unchanged V2 Decimal engine.

No database connection, inference, source retrieval, or app startup occurs here.
"""
import json
from datetime import date
from pathlib import Path

from neocloud.catalog import COMPANIES
from neocloud.hut_reference import reference
from neocloud.risk import comparison
from neocloud.v2_engine import new_v2_run

AS_OF = date(2026, 10, 17)
SCENARIOS = ('Base', 'Downside', 'Tight credit')
SHOCKS = (0, 100, 200, 300)


def build():
    # Do not seed reported project facts into synthetic consolidated scenarios.
    run = new_v2_run(list(COMPANIES), 'simulated', AS_OF)
    return {
        'as_of': str(AS_OF),
        'disclosure': 'Synthetic teaching scenarios, not company forecasts or current financials. '
                      'Company labels demonstrate the interface; identical assumptions are intentional. '
                      'HUT disclosure excerpts are historical references and are displayed separately.',
        'companies': COMPANIES,
        'cases': {f'{scenario}:{shock}': comparison(run, AS_OF, scenario, shock)
                  for scenario in SCENARIOS for shock in SHOCKS},
        'reference': reference(),
    }


if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'preview' / 'data.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(build(), separators=(',', ':'), sort_keys=True) + '\n')
    print(f'Wrote {target.relative_to(target.parents[1])} ({target.stat().st_size:,} bytes)')
