#!/usr/bin/env python3
"""Build self-contained GitHub profile SVGs using only Python's standard library."""
import argparse
import calendar
import hashlib
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


def build_svg(config, stats, rows, avatar, mobile=False, tones=None):
    width = 360 if mobile else 1120
    x = 20 if mobile else 518
    right = width - (20 if mobile else 28)
    char = 8.7 if mobile else 9.6
    font_size = 14.5 if mobile else 16
    start_y = 382 if mobile else 30
    line = 24
    height = start_y + len(rows) * line + 65
    title = f'{config["display_name"]} — perfil de terminal'
    description = '; '.join(f'{key}: {value}' for kind, key, value in rows if kind == 'field')
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
              f'<title id="title">{escape(title)}</title>',
              f'<desc id="desc">{escape(description)}</desc>',
              f'<rect width="{width}" height="{height}" fill="{BG}"/>',
              f'<g font-family="{FONT}" xml:space="preserve">']
    columns = max(len(row) for row in avatar)
    avatar_width = 320 if mobile else 448
    avatar_char = avatar_width / columns
    avatar_size = avatar_char / .6
    avatar_x = 20 if mobile else 29
    avatar_line = avatar_width / len(avatar)
    avatar_top = 20 if mobile else max(20, (height-avatar_width)/2)
    avatar_y = avatar_top + avatar_size
    for index, row in enumerate(avatar):
        y = round(avatar_y + index*avatar_line, 2)
        if tones is None:
            chunks.append(text(avatar_x, y, row, avatar_size, '#aebbc9',
                               textLength=len(row)*avatar_char, lengthAdjust='spacingAndGlyphs'))
            continue
        # Equal-tone runs keep the SVG compact while preserving every source cell.
        levels = [min(255, round(value/8)*8) for value in tones[index]]
        start = 0
        while start < len(row):
            end = start + 1
            while end < len(row) and levels[end] == levels[start]:
                end += 1
            gray = levels[start]
            chunks.append(text(round(avatar_x + start*avatar_char, 3), y,
                               row[start:end], avatar_size, f'rgb({gray},{gray},{gray})',
                               textLength=(end-start)*avatar_char, lengthAdjust='spacingAndGlyphs'))
            start = end
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


def build_readme(config, rows, versions=None):
    versions = versions or {}
    desktop_version = versions.get('desktop', '')
    mobile_version = versions.get('mobile', '')
    alt = '; '.join(f'{key}: {value}' for kind, key, value in rows if kind == 'field')
    links = ' · '.join(f'[{label}]({url})' for label, url in config.get('links', []))
    plain = '\n'.join(f'{key}: {value}' if value else key for kind, key, value in rows if kind not in ('rule', 'blank'))
    return f'''<!-- Generated by scripts/update_profile.py. Edit profile.json to customize. -->
<picture>
  <source media="(max-width: 600px)" srcset="assets/neofetch-mobile.svg?v={mobile_version}">
  <img src="assets/neofetch.svg?v={desktop_version}" width="1120" alt="{escape(config['display_name'] + ' — ' + alt, quote=True)}">
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
    tones_path = ROOT/'assets/avatar-tones.json'
    tones = json.loads(tones_path.read_text(encoding='utf-8')) if tones_path.exists() else None
    if tones is not None and (len(tones) != len(avatar)
                              or any(len(t) != len(row) for t, row in zip(tones, avatar))):
        raise ValueError('avatar.txt e avatar-tones.json devem ter as mesmas dimensões.')
    # Build everything before replacing files: API/config errors leave prior assets intact.
    desktop_svg = build_svg(config, stats, rows, avatar, tones=tones)
    mobile_svg = build_svg(config, stats, rows, avatar, mobile=True, tones=tones)
    versions = {key: hashlib.sha256(svg.encode('utf-8')).hexdigest()[:12]
                for key, svg in [('desktop', desktop_svg), ('mobile', mobile_svg)]}
    outputs = {
        'assets/neofetch.svg': desktop_svg,
        'assets/neofetch-mobile.svg': mobile_svg,
        'README.md': build_readme(config, rows, versions),
        'assets/stats.json': json.dumps(stats, indent=2, ensure_ascii=False)+'\n',
    }
    for name, content in outputs.items():
        (ROOT/name).write_text(content, encoding='utf-8', newline='\n')
    print('Updated desktop/mobile SVGs, README and public stats.')


if __name__ == '__main__':
    main()
