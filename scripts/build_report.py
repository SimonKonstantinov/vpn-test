"""Render this project's plain Markdown report without external dependencies."""
import html
import re
from pathlib import Path


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)


def main():
    root = Path(__file__).resolve().parents[1]
    parts = []
    for line in (root / 'docs/REPORT.md').read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        match = re.match(r'^(#{1,3}) (.*)$', line)
        if match:
            level = len(match[1])
            parts.append(f'<h{level}>{inline(match[2])}</h{level}>')
        elif line.startswith('- '):
            parts.append('<p class="item">• ' + inline(line[2:]) + '</p>')
        else:
            parts.append('<p>' + inline(line) + '</p>')
    document = '''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CompassVPN — итоговый отчёт</title>
<style>body{font:17px/1.65 system-ui,sans-serif;color:#193044;background:#f1f5f8;margin:0}main{max-width:1000px;margin:36px auto;padding:40px;background:white;border-radius:14px}h1{font-size:34px;line-height:1.25}h2{margin-top:40px;border-top:1px solid #d5e1e9;padding-top:20px}h3{color:#185978}code{background:#eef3f6;padding:2px 5px;overflow-wrap:anywhere}a{color:#005c96}.item{margin:8px 0 8px 20px}@media print{body{background:white;font-size:11pt}main{margin:0;padding:0}h2,h3{break-after:avoid}}</style></head><body><main>'''+ '\n'.join(parts)+'</main></body></html>'
    (root / 'docs/REPORT.html').write_text(document, encoding='utf-8')


if __name__ == '__main__':
    main()
