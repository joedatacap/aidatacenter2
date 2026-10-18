"""Bounded real Crusoe research, with an explicit nonpersistent diagnostic repository."""
import argparse
import asyncio
import json
from pathlib import Path
from neocloud.crusoe import Crusoe
from neocloud.engine import Engine, new_run
from neocloud.repository import MemoryRepository


async def investigate(tickers, output):
    model = Crusoe()
    verification = await model.verify()
    repo = MemoryRepository()
    engine = Engine(repo, model)
    run = new_run(tickers)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps({'inference': verification, 'storage': repo.mode}), flush=True)
    while run['status'] in ('queued', 'running'):
        await engine.step(run)
        path.write_text(json.dumps(run, indent=2)+'\n')
        print(json.dumps({'status': run['status'], 'tasks': len(run['tasks']),
                          'evidence': len(run['evidence']), 'instruments': len(run['instruments']),
                          'budgets': run['budgets']}), flush=True)
        await asyncio.sleep(.5)
    return run


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tickers', nargs='+', choices=['CRWV', 'NBIS', 'IREN', 'BTDR'])
    parser.add_argument('--output', default='work/live-investigation.json')
    args = parser.parse_args()
    if len(args.tickers) > 2:
        parser.error('Select one or two tickers')
    asyncio.run(investigate(list(dict.fromkeys(args.tickers)), args.output))
