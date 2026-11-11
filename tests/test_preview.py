"""The public bundle must stay deterministic and use original finance outputs."""
import json
from pathlib import Path

from scripts.build_preview import AS_OF, SCENARIOS, SHOCKS, build
from neocloud.risk import comparison
from neocloud.v2_engine import new_v2_run


def test_committed_preview_matches_engine_and_contains_no_reported_scenario_inputs():
    data = build()
    assert json.loads(Path('preview/scenarios/data.json').read_text()) == data
    run = new_v2_run(list(data['companies']), 'simulated', AS_OF)
    for scenario in SCENARIOS:
        for shock in SHOCKS:
            case = data['cases'][f'{scenario}:{shock}']
            assert case == comparison(run, AS_OF, scenario, shock)
            for report in case['tickers'].values():
                assert all(f['provenance'] == 'assumption' for f in report['funding'])
                assert all(b['quote'] is None for b in report['debt_cost'])
                assert not report['contracts']
    # Reported project financing stays in its own source-backed reference section.
    assert data['reference']['evidence']
    assert data['cases']['Base:200']['tickers']['HUT']['leverage']['known_principal_by_currency'] == {'USD': '500000000'}
