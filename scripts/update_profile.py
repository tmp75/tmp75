#!/usr/bin/env python3
"""Build self-contained GitHub profile SVGs using only Python's standard library."""
import argparse
import calendar
from datetime import date, datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BG = '#161b22'
FG = '#b7c7d9'
KEY = '#c99c6b'
DIM = '#687483'
FONT = "Consolas, 'Liberation Mono', Menlo, monospace"


def calendar_age(start, end):
    if start > end:
        raise ValueError('A data inicial não pode estar no futuro.')
    months = (end.year - start.year) * 12 + end.month - start.month
    def anniversary(n):
        year, month0 = divmod(start.year * 12 + start.month - 1 + n, 12)
        month = month0 + 1
        return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))
    if anniversary(months) > end:
        months -= 1
    years, remaining = divmod(months, 12)
    days = (end - anniversary(months)).days
    return f'{years} anos, {remaining} meses, {days} dias'


def get_json(endpoint):
    headers = {
        'User-Agent': 'github-neofetch-profile',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    # The job's short-lived token avoids shared-runner anonymous rate limits.
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request('https://api.github.com/' + endpoint, headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_stats(username):
    profile = get_json(f'users/{username}')
    repos = []
    page = 1
    while True:
        batch = get_json(f'users/{username}/repos?type=owner&per_page=100&page={page}')
        repos.extend(r for r in batch if not r.get('private', False)
                     and r.get('visibility', 'public') == 'public')
        if len(batch) < 100:
            break
        page += 1
    return {
        'created_at': profile['created_at'],
        'public_repos': profile['public_repos'],
        'stars_owned': sum(r['stargazers_count'] for r in repos if not r['fork']),
        'followers': profile['followers'],
        'as_of': datetime.now(timezone.utc).date().isoformat(),
    }


def build_rows(config, stats, today):
    birthday = os.environ.get('PROFILE_BIRTH_DATE') or config.get('birth_date')
    start = date.fromisoformat(birthday or stats['created_at'][:10])
    uptime_label = 'Uptime' if birthday else 'Uptime.GitHub'
    system = [list(pair) for pair in config['system']]
    system.insert(1, [uptime_label, calendar_age(start, today)])
    rows = [('header', config['display_name'] + '@github', ''), ('rule', '', '')]
    rows += [('field', k, v) for k, v in system]
    rows += [('blank', '', '')]
    rows += [('field', k, v) for k, v in config['languages']]
    rows += [('blank', '', ''), ('section', 'Contact', '')]
    rows += [('field', k, v) for k, v in config['contact']]
    rows += [('blank', '', ''), ('section', 'GitHub Stats', '')]
    rows += [('field', 'Repos.Public', str(stats['public_repos'])),
             ('field', 'Stars.Owned', str(stats['stars_owned'])),
             ('field', 'Followers', str(stats['followers']))]
    return rows


def text(x, y, value, size=16, fill=FG, **attrs):
    extra = ' '.join(f'{key.replace("_", "-")}="{escape(str(val), quote=True)}"'
                     for key, val in attrs.items())
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>'
            f'{escape(str(value))}</text>')


def build_svg(config, stats, rows, avatar, mobile=False):
    width = 460 if mobile else 1120
    x = 26 if mobile else 518
    right = width - 28
    char = 8.1 if mobile else 9.6
    font_size = 13.5 if mobile else 16
    start_y = 495 if mobile else 100
    line = 24
    height = start_y + len(rows) * line + 65
    title = f'{config["display_name"]} — perfil de terminal'
    description = '; '.join(f'{key}: {value}' for kind, key, value in rows if kind == 'field')
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
              f'<title id="title">{escape(title)}</title>',
              f'<desc id="desc">{escape(description)}</desc>',
              f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="{BG}" stroke="#30363d"/>',
              f'<path d="M1 49H{width-1}" stroke="#30363d"/>',
              f'<g font-family="{FONT}" xml:space="preserve">']
    for index, color in enumerate(['#b87f79', '#b8a477', '#83a18d']):
        chunks.append(f'<circle cx="{25+index*19}" cy="25" r="4.5" fill="{color}"/>')
    chunks.append(text(width/2, 30, f'~/{config["username"]}  —  neofetch', 12, DIM, text_anchor='middle'))
    avatar_size = 7.2 if mobile else 9.9
    avatar_x = 65 if mobile else 29
    avatar_y = 86 if mobile else 94
    avatar_line = 8 if mobile else 11.5
    for index, row in enumerate(avatar):
        chunks.append(text(avatar_x, round(avatar_y+index*avatar_line, 2), row,
                           avatar_size, '#aebbc9', letter_spacing='0'))
    for index, (kind, key, value) in enumerate(rows):
        y = start_y + index * line
        if kind == 'blank':
            continue
        if kind == 'header':
            chunks.append(text(x, y, key, font_size, '#d3dce6', font_weight='700'))
        elif kind == 'rule':
            chunks.append(f'<path d="M{x} {y-8}H{right}" stroke="#46515e"/>')
        elif kind == 'section':
            chunks.append(text(x, y, key, font_size, '#c6ced8'))
            rule_start = x + (len(key)+2)*char
            chunks.append(f'<path d="M{rule_start} {y-5}H{right}" stroke="#46515e"/>')
        else:
            # Shrink a long row, preserving column separation and avoiding clipping.
            available_chars = (right-x) / char
            needed_chars = len(key)+len(value)+4
            scale = min(1, available_chars/needed_chars)
            actual_size, actual_char = font_size*scale, char*scale
            dots_x = x+(len(key)+2)*actual_char
            value_x = right-len(value)*actual_char
            dot_count = max(0, int((value_x-dots_x)/actual_char)-1)
            chunks.append(text(x, y, key+':', actual_size, KEY))
            if dot_count:
                chunks.append(text(dots_x, y, '.'*dot_count, actual_size, '#455160'))
            chunks.append(text(right, y, value, actual_size, FG, text_anchor='end'))
    palette_y = start_y + len(rows)*line + 7
    colors = ['#414b57','#b87f79','#a6b68d','#c9ae7d','#89aace','#b29fbe','#87b6bc','#c9d2dc']
    for index, color in enumerate(colors):
        chunks.append(f'<rect x="{x+index*25}" y="{palette_y}" width="25" height="15" fill="{color}"/>')
    chunks.append(text(x, palette_y+36, 'sync ' + stats['as_of'] + ' UTC', 10, DIM))
    chunks += ['</g>', '</svg>']
    return '\n'.join(chunks)+'\n'


def build_readme(config, rows):
    alt = '; '.join(f'{key}: {value}' for kind, key, value in rows if kind == 'field')
    links = ' · '.join(f'[{label}]({url})' for label, url in config.get('links', []))
    plain = '\n'.join(f'{key}: {value}' if value else key for kind, key, value in rows if kind not in ('rule', 'blank'))
    return f'''<!-- Generated by scripts/update_profile.py. Edit profile.json to customize. -->
<picture>
  <source media="(max-width: 600px)" srcset="assets/neofetch-mobile.svg">
  <img src="assets/neofetch.svg" width="1120" alt="{escape(config['display_name'] + ' — ' + alt, quote=True)}">
</picture>

{links}

<details>
<summary>Versão em texto</summary>

```text
{plain}
```

</details>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Fetch current public GitHub stats')
    parser.add_argument('--date', help='Date override (YYYY-MM-DD) for deterministic previews')
    args = parser.parse_args()
    config = json.loads((ROOT/'profile.json').read_text(encoding='utf-8'))
    stats_path = ROOT/'assets/stats.json'
    stats = fetch_stats(config['username']) if args.refresh else json.loads(stats_path.read_text(encoding='utf-8'))
    today = date.fromisoformat(args.date) if args.date else datetime.now(timezone.utc).date()
    rows = build_rows(config, stats, today)
    avatar = (ROOT/'assets/avatar.txt').read_text(encoding='utf-8').splitlines()
    # Build everything before replacing files: API/config errors leave prior assets intact.
    outputs = {
        'assets/neofetch.svg': build_svg(config, stats, rows, avatar),
        'assets/neofetch-mobile.svg': build_svg(config, stats, rows, avatar, mobile=True),
        'README.md': build_readme(config, rows),
        'assets/stats.json': json.dumps(stats, indent=2, ensure_ascii=False)+'\n',
    }
    for name, content in outputs.items():
        (ROOT/name).write_text(content, encoding='utf-8', newline='\n')
    print('Updated desktop/mobile SVGs, README and public stats.')


if __name__ == '__main__':
    main()
