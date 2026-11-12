"""Mirror static assets under the requested path without changing other sites."""
from pathlib import Path
from shutil import copytree

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    target = ROOT / 'work' / 'cloudflare-preview' / 'neoclouddebt'
    copytree(ROOT / 'preview', target, dirs_exist_ok=True)
    # Cloudflare reads _headers from the asset directory root.
    (target.parent / '_headers').write_text((ROOT / 'preview' / '_headers').read_text())
    print('Staged work/cloudflare-preview/neoclouddebt/')
