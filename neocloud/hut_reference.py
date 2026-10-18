"""Curated exact SEC excerpts. Source matching is distinct from runtime audit approval."""
import json
from copy import deepcopy
from pathlib import Path


def reference():
    return json.loads(Path(__file__).with_name('data').joinpath('hut_reference.json').read_text())


def seed(run):
    data = reference()
    ids = {e['id']: run['id'] + ':' + e['id'] for e in data['evidence']}
    for e in data['evidence']:
        e['id'] = ids[e['id']]
        e['provenance'] = 'fixture' if run['mode'] == 'simulated' else 'live'
        e['task_id'] = run['tasks'][0]['id']
        e['claim'] += ' [Curated previously retrieved reference; not a new fetch in this run]'
        run['evidence'].append(e)
    for item in data['instruments']:
        item['evidence_ids'] = [ids[e] for e in item['evidence_ids']]
        if run['mode'] == 'simulated':
            item.update(provenance='fixture', verification_status='fixture')
        run['instruments'].append(item)
    for kind in ('contracts', 'repayments'):
        for item in data[kind]:
            item['evidence_ids'] = [ids[e] for e in item['evidence_ids']]
            if run['mode'] == 'simulated':
                item.update(provenance='fixture', status='fixture')
            run['risk'][kind].append(item)
