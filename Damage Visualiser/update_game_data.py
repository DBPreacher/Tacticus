#!/usr/bin/env python3
"""Download the Tacticus game data from tacticustable.com, but only when the
game version has changed since the last download.

    python -X utf8 update_game_data.py          # download if the version changed
    python -X utf8 update_game_data.py --force  # download anyway

The data (about 11 MB) is cached in cache/gameinfo.json, which git ignores.
See INSTRUCTIONS.md.
"""
import argparse, json, os, sys, urllib.request

API = 'https://api.tacticustable.com/game-info'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache', 'gameinfo.json')
HEADERS = {'User-Agent': 'DBPreacher-DamageVisualiser/1.0', 'Origin': 'https://www.tacticustable.com'}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def cached_version():
    if not os.path.exists(CACHE):
        return None
    with open(CACHE, encoding='utf-8') as f:
        g = json.load(f)
    return g.get('data', g).get('version')


def update_relic_owners():
    """Which characters can equip each relic. The game data doesn't say, so this reads the wiki's
    Category:Relics pages ('== Shared Relic ==' lists characters; '== X Unique Relic ==' names one)
    and writes relic_owners.csv. Check it after a patch that adds relics."""
    import csv, re
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'LRE Script'))
    import wiki_audit as wa
    data = wa.api_get({'action': 'query', 'list': 'categorymembers', 'cmtitle': 'Category:Relics', 'cmlimit': '500'})
    titles = sorted(m['title'] for m in data['query']['categorymembers'])
    pages = wa.fetch_wikitext(titles)
    rows = []
    for relic in titles:
        text = pages.get(relic, '')
        unique = re.search(r'==\s*(.+?)\s+Unique Relic\s*==', text)
        if unique:
            owners = [re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', unique.group(1)).strip()]
        else:
            block = re.search(r'==\s*Shared Relic\s*==(.*?)(?:\n==|\Z)', text, re.S)
            owners = re.findall(r'\*\s*\[\[([^\]|]+)', block.group(1)) if block else []
        if not owners:
            print(f'WARNING - no owner found on the wiki page for relic {relic}')
        rows += [(relic, o.strip()) for o in owners]
    path = os.path.join(HERE, 'relic_owners.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Relic', 'Character'])
        w.writerows(rows)
    print(f'relic_owners.csv: {len(titles)} relics, {len(rows)} relic/character pairs (from the wiki).')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='download even if the version is unchanged')
    ap.add_argument('--relics', action='store_true', help='only refresh relic_owners.csv from the wiki')
    args = ap.parse_args()
    if args.relics:
        update_relic_owners()
        return

    live = json.loads(get(API + '/version'))['version']
    have = cached_version()
    print(f'tacticustable game version: {live}   cached: {have or "none"}')
    if live == have and not args.force:
        print('Cache is up to date, nothing downloaded.')
        return
    raw = get(API)
    g = json.loads(raw)
    data = g.get('data', g)
    if not data.get('heroes'):
        sys.exit('Download has no heroes in it; cache left unchanged.')
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, 'wb') as f:
        f.write(raw)
    print(f'Saved {len(raw) / 1e6:.1f} MB: version {data["version"]}, {len(data["heroes"])} heroes.')
    update_relic_owners()


if __name__ == '__main__':
    main()
