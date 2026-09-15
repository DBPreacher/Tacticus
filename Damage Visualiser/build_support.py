"""
build_support.py - builds support-map.html, the Support Map (Attack side).

Runs support_model.py for every tier and switch combination (the same 48 settings as the Roster Battle
Map), in parallel, and writes the page from support_template.html. Run it after build_map.py:

    python -X utf8 build_support.py
    python -X utf8 build_support.py --page-only   # design changes: reuse the last build's numbers

See INSTRUCTIONS.md ("Support Map").
"""
import argparse, csv, json, os, re, sys, time
from multiprocessing import Pool
import build_map as bm
import support_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'support_template.html')
OUT = os.path.join(HERE, 'support-map.html')

_cache = {}


def _read(path, key):
    with open(path, newline='', encoding='utf-8') as f:
        return {r[key]: r for r in csv.DictReader(f)}


def _tier(tier_key):
    """set the tier's globals and return (units, specs), cached per worker process (read-only: never
    rewrites the ability CSVs, so workers can run side by side)"""
    t = next(x for x in bm.TIERS if x['key'] == tier_key)
    bm.set_tier(t)
    if tier_key not in _cache:
        g, units = bm.load()
        specs = bm.build_specs(units, _read(bm.ACTIVES_CSV, 'Name'), _read(bm.PASSIVES_CSV, 'Name'), _read(bm.RELICS_CSV, 'Relic'))
        _cache[tier_key] = (units, specs)
    return _cache[tier_key]


def job(args):
    tier_key, key, lv, trig, act, gear = args
    units, specs = _tier(tier_key)
    idx = {u['name']: i for i, u in enumerate(units)}
    res = sm.run(units, specs, sm.load_rows(), tier_key, lv, trig, act, gear)
    return tier_key, key, {ri: [[idx[n], round(b * 1000), round(s * 1000)] for n, b, s in al] for ri, al in res.items()}


def write_page(data):
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('support_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page-only', action='store_true', help="rebuild the page from the template with the last build's numbers")
    if ap.parse_args().page_only:
        with open(OUT, encoding='utf-8') as f:
            m = re.search(r'const DATA = (\{.*?\});\n', f.read(), re.S)
        if not m:
            sys.exit('No numbers in support-map.html yet: run a full build first.')
        write_page(json.loads(m.group(1)))
        print('Rebuilt support-map.html from the template (numbers unchanged).')
        return
    start = time.time()
    rows = sm.load_rows()
    jobs, tiers, vals = [], [], {}
    for t in bm.TIERS:
        bm.set_tier(t)
        g, units = bm.load()
        U = {u['name']: u for u in units}
        tiers.append(dict(key=t['key'], label=t['label'], levels=list(t['levels'])))
        for key, trig, lv, act, gear in bm.scenario_keys():
            if lv:
                jobs.append((t['key'], key, lv, trig, act, gear))
        for ri, r in enumerate(rows):
            ab, relic = sm.row_ability(U, r)
            if relic and t['key'] != 'mythic':
                continue
            vals.setdefault(ri, {})[t['key']] = {lv: sm.describe(r['Effect'], ab, relic, lv) for lv in t['levels']}
    chars = [dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in units]
    first = {u['name']: u for u in units}
    supports = [dict(name=r['Name'], src=r['Source'], ability=r['Ability'], alliance=first[r['Name']]['alliance'],
                     faction=first[r['Name']]['faction'], receives=r['Receives'], reach=r['Reach'], lasts=r['Lasts'],
                     cond=r['Condition'], notes=r['Notes'], text=r['Ability_Text'], vals=vals.get(ri, {}))
                for ri, r in enumerate(rows)]
    data = dict(version=g['version'], tiers=tiers, chars=chars, supports=supports, spacing=sm.SPACING,
                fixed=sm.FIXED_REACH, s={t['key']: {} for t in tiers})
    with Pool(min(len(jobs), os.cpu_count() or 4)) as pool:
        for tier_key, key, res in pool.imap_unordered(job, jobs):
            data['s'][tier_key][key] = res
    write_page(data)
    print(f'Built support-map.html: {len(rows)} support abilities, {len(jobs)} settings, '
          f'game version {g["version"]}, {time.time() - start:.0f}s.')


if __name__ == '__main__':
    main()
