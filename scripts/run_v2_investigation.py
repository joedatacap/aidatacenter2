"""Bounded real V2 runtime proof; uses TEST_DATABASE_URL only when explicitly requested.

Never probes Neon networking. Default storage is labeled development memory.
"""
import argparse
import asyncio
import json
import os
from datetime import date
from pathlib import Path
from neocloud.crusoe import Crusoe
from neocloud.routing import RoleRouter
from neocloud.repository import MemoryRepository, PostgresRepository
from neocloud.v2_engine import V2Engine, new_v2_run
from neocloud.hut_reference import seed


async def main(args):
    model = Crusoe()
    model.router = RoleRouter(model)
    routes = await model.router.verify()
    if not routes['routes']['manager']['verified']:
        raise RuntimeError('No verified manager route')
    repo = PostgresRepository(os.environ['TEST_DATABASE_URL']) if args.test_postgres else MemoryRepository()
    await repo.initialize()
    run = new_v2_run(args.tickers, as_of=date.fromisoformat(args.as_of))
    if 'HUT' in args.tickers:
        seed(run)
    await repo.save(run)
    engine = V2Engine(repo, model)
    try:
        for _ in range(100):
            await engine.step(run)
            if run['status'] not in ('running', 'queued'):
                break
            await asyncio.sleep(.1)
        saved = await repo.get(run['id'])
        saved.pop('source_cache', None)
        Path(args.output).write_text(json.dumps({'storage': repo.mode, 'routes': routes, 'run': saved}, indent=2))
        print(json.dumps({'id': run['id'], 'status': run['status'], 'budgets': run['budgets'],
                          'tasks': len(run['tasks']), 'recursive_children': sum(e['kind'] == 'recursive_child' for e in run['events'])}))
    finally:
        await repo.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tickers', nargs='+', choices=['CRWV', 'NBIS', 'IREN', 'BTDR', 'HUT'])
    parser.add_argument('--as-of', default='2026-10-17')
    parser.add_argument('--test-postgres', action='store_true')
    parser.add_argument('--output', default='work/v2-live.json')
    asyncio.run(main(parser.parse_args()))
