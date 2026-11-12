"""Validate curated primary-source records and export the read-only directory."""
import json
from pathlib import Path
from neocloud.directory import build_directory

ROOT = Path(__file__).resolve().parents[1]


def build():
    raw = json.loads((ROOT / 'neocloud/data/debt_directory.json').read_text())
    return build_directory(raw)


if __name__ == '__main__':
    target = ROOT / 'preview/data.json'
    target.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n')
    print(f'Validated and exported {target}')
