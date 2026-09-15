"""
build_support.py - builds support-map.html, the Support Map (Attack and Defence sides).

Runs support_model.py for every tier and switch combination (the same 48 settings as the Roster Battle
Map; the Defence side for both Enemy focus settings), in parallel, and writes the page from
support_template.html. Run it after build_map.py:

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
    side, focus, tier_key, key, lv, trig, act, gear = args
    units, specs = _tier(tier_key)
    idx = {u['name']: i for i, u in enumerate(units)}
    if side == 'attack':
        bm.ATTACKS_PER_TURN = 5
        res = sm.run(units, specs, sm.load_rows('Attack'), tier_key, lv, trig, act, gear)
    else:
        bm.ATTACKS_PER_TURN = sm.FOCUS[focus]
        res = sm.run_defence(units, specs, sm.load_rows('Defence'), tier_key, lv, trig, act, gear)
    bm.ATTACKS_PER_TURN = 5
    return side, focus, tier_key, key, {ri: pack(al, idx) for ri, al in res.items()}


def pack(allies, idx):
    """one support's allies, compactly: v = [ally, boost x 1000, ...]; s = the share of the roster its enemies
    are, x 1000 (left out when 1000, a list when it differs by ally); c = positions that reached the horizon"""
    out = dict(v=[x for al in allies for x in (idx[al[0]], round(al[1] * 1000))])
    shares = [round(al[2] * 1000) for al in allies]
    if any(s != 1000 for s in shares):
        out['s'] = shares[0] if len(set(shares)) == 1 else shares
    capped = [i for i, al in enumerate(allies) if len(al) > 3 and al[3]]
    if capped:
        out['c'] = capped
    return out


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
    rows, drows = sm.load_rows('Attack'), sm.load_rows('Defence')
    jobs, tiers, vals, dvals = [], [], {}, {}
    for t in bm.TIERS:
        bm.set_tier(t)
        g, units = bm.load()
        U = {u['name']: u for u in units}
        tiers.append(dict(key=t['key'], label=t['label'], levels=list(t['levels'])))
        for key, trig, lv, act, gear in bm.scenario_keys():
            if lv:
                jobs.append(('attack', None, t['key'], key, lv, trig, act, gear))
                for focus in sm.FOCUS:
                    jobs.append(('defence', focus, t['key'], key, lv, trig, act, gear))
        for ri, r in enumerate(rows):
            ab, relic = sm.row_ability(U, r)
            if relic and t['key'] != 'mythic':
                continue
            vals.setdefault(ri, {})[t['key']] = {lv: sm.describe(r['Effect'], ab, relic, lv) for lv in t['levels']}
        for ri, r in enumerate(drows):
            ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(U, r)
            if relic and t['key'] != 'mythic':
                continue
            dvals.setdefault(ri, {})[t['key']] = {lv: sm.describe_defence(r['Effect'], U[r['Name']], ab, relic, lv) for lv in t['levels']}
    chars = [dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in units]
    first = {u['name']: u for u in units}
    card = lambda r, v: dict(name=r['Name'], src=r['Source'], ability=r['Ability'], alliance=first[r['Name']]['alliance'],
                             faction=first[r['Name']]['faction'], receives=r['Receives'], reach=r['Reach'], lasts=r['Lasts'],
                             cond=r['Condition'], notes=r['Notes'], text=r['Ability_Text'], vals=v)
    data = dict(version=g['version'], tiers=tiers, chars=chars, spacing=sm.SPACING, fixed=sm.FIXED_REACH,
                focus=sm.FOCUS, horizon=sm.HORIZON_TURNS,
                supports=[card(r, vals.get(ri, {})) for ri, r in enumerate(rows)],
                dsupports=[card(r, dvals.get(ri, {})) for ri, r in enumerate(drows)],
                s={t['key']: {} for t in tiers}, d={t['key']: {} for t in tiers})
    with Pool(min(len(jobs), os.cpu_count() or 4)) as pool:
        for side, focus, tier_key, key, res in pool.imap_unordered(job, jobs):
            if side == 'attack':
                data['s'][tier_key][key] = res
            else:
                data['d'][tier_key].setdefault(key, {})[focus] = res
    write_page(data)
    print(f'Built support-map.html: {len(rows)} Attack and {len(drows)} Defence support abilities, {len(jobs)} runs, '
          f'game version {g["version"]}, {time.time() - start:.0f}s.')


if __name__ == '__main__':
    main()
