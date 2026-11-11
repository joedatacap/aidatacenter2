"""Bundle the existing preview as one HTML file that works offline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(target=None):
    preview = ROOT / 'preview'
    html = (preview / 'index.html').read_text()
    css = (preview / 'preview.css').read_text()
    js = (preview / 'preview.js').read_text()
    data = (preview / 'data.json').read_text()
    html = html.replace('<link rel="stylesheet" href="./preview.css">', '<style>' + css + '</style>')
    html = html.replace('<script src="./preview.js" defer></script>', '')
    html = html.replace('href="./"', 'href="#"')
    # Data cannot close its script element, even if a future source excerpt contains markup.
    html = html.replace('</body>', '<script id="preview-data" type="application/json">' +
                        data.replace('<', '\\u003c') + '</script><script>' +
                        js.replace('</script', '<\\/script') + '</script></body>')
    target = target or ROOT / 'work' / 'NeoCloud-Interactive-Preview.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)
    return target


if __name__ == '__main__':
    print(build())
