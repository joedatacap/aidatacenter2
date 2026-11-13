"""Build the independent website V2 workspace from the validated evidence ledger."""
import json
from pathlib import Path

from neocloud.directory import build_directory

ROOT = Path(__file__).resolve().parents[1]


def build():
    target = ROOT / "v2-preview"
    data = build_directory(json.loads((ROOT / "neocloud/data/debt_directory.json").read_text()))
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (target / "data.json").write_text(encoded + "\n")
    html = (target / "index.html").read_text()
    html = html.replace('<link rel="stylesheet" href="./workspace.css">',
                        '<style>' + (target / "workspace.css").read_text() + '</style>')
    html = html.replace('<script src="./workspace.js" defer></script>', '')
    html = html.replace('</body>', '<script id="workspace-data" type="application/json">' +
                        encoded.replace('<', '\\u003c') + '</script><script>' +
                        (target / "workspace.js").read_text().replace('</script', '<\\/script') +
                        '</script></body>')
    output = ROOT / "work/NeoCloud-V2-Workspace.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html)
    return output


if __name__ == "__main__":
    print(build())
