"""
build_faction.py - the Faction Battle Map page.

Runs `faction_data.py`, inlines the faction badges from `faction_badges/`, and drops both into
`faction_template.html`. The page is one self-contained file with no fetches in it, the same as the
Roster Battle Map, so it can be opened from disk or dropped straight into a video.

    python -X utf8 build_faction.py

Edit `faction_template.html`, never `faction-battle-map.html`.

See PLAN.md, "Faction comparison".
"""
import base64
import json
import os

import faction_data as fd

HERE = os.path.dirname(os.path.abspath(__file__))
BADGES = os.path.join(HERE, 'faction_badges')
TEMPLATE = os.path.join(HERE, 'faction_template.html')
OUT = os.path.join(HERE, 'faction-battle-map.html')
EXPLAIN = os.path.join(HERE, 'explain_template.html')
OUT_EXPLAIN = os.path.join(HERE, 'faction-explained.html')


def badges(factions):
    """{faction: data URI}. A missing badge is not fatal - the page falls back to the coloured ring -
    but it is worth saying out loud, because a faction with no mark is easy to miss on a chart."""
    out, missing = {}, []
    for f in factions:
        path = os.path.join(BADGES, f + '.png')
        if not os.path.exists(path):
            missing.append(f)
            continue
        with open(path, 'rb') as fh:
            out[f] = 'data:image/png;base64,' + base64.b64encode(fh.read()).decode('ascii')
    if missing:
        print('WARNING - no badge art for: ' + ', '.join(missing) + ' (run faction_badges.py)')
    return out


def main():
    data, version = fd.build()
    fd.report(data)
    payload = dict(version=version,
                   setting=dict(tier='mythic', level=fd.bm.ABILITY_LEVELS[1], adjacent=fd.gr.ADJACENT_ALLIES,
                                cap=fd.CAP),
                   factions=data)
    with open(fd.OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=1)
    art = badges(sorted(data))
    for src, out in ((TEMPLATE, OUT), (EXPLAIN, OUT_EXPLAIN)):
        with open(src, encoding='utf-8') as f:
            html = f.read()
        html = html.replace('/*DATA*/', json.dumps(payload, separators=(',', ':')))
        html = html.replace('/*BADGES*/', json.dumps(art, separators=(',', ':')))
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
    playable = sum(1 for d in data.values() if d['teams'])
    fives = sum(len(d['teams']) for d in data.values())
    print(f'\nBuilt faction-battle-map.html and faction-explained.html: {playable} factions, {fives} fives, '
          f'game version {version}. {os.path.getsize(OUT) / 1024:.0f} KB and '
          f'{os.path.getsize(OUT_EXPLAIN) / 1024:.0f} KB.')


if __name__ == '__main__':
    main()
