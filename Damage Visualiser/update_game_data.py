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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='download even if the version is unchanged')
    args = ap.parse_args()

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


if __name__ == '__main__':
    main()
