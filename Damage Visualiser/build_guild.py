"""
build_guild.py - builds guild-raid.html, the Guild Raid page ("the best five for this boss").

Runs guild_raid.py's search for every boss and every switch combination (the same tiers and scenarios as
the Roster Battle Map, with the side battles on and off), in parallel, and writes the page from
guild_template.html. Run it after build_map.py:

    python -X utf8 build_guild.py
    python -X utf8 build_guild.py --page-only   # design changes: reuse the last build's numbers

See INSTRUCTIONS.md ("Guild Raid").
"""
import argparse, csv, json, os, re, sys, time
from multiprocessing import Pool
import build_map as bm
import support_model as sm
import guild_raid as gr

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'guild_template.html')
OUT = os.path.join(HERE, 'guild-raid.html')
ALTS = 8                      # how many characters just outside the five the page lists

_cache = {}


def _read(path, key):
    with open(path, newline='', encoding='utf-8') as f:
        return {r[key]: r for r in csv.DictReader(f)}


def _tier(tier_key):
    """the roster at one tier, cached per worker process (read-only: never rewrites the ability CSVs)"""
    t = next(x for x in bm.TIERS if x['key'] == tier_key)
    bm.set_tier(t)
    if tier_key not in _cache:
        g, units = bm.load()
        specs = bm.build_specs(units, _read(bm.ACTIVES_CSV, 'Name'), _read(bm.PASSIVES_CSV, 'Name'),
                               _read(bm.RELICS_CSV, 'Relic'))
        _cache[tier_key] = (units, specs)
    return _cache[tier_key]


TIER_NAMES = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Mythic']


def fight_list(g):
    """every boss fight, in the game's own order. A tier holds several sets, and the game names them
    the way players do: Mythic 1, Mythic 2, Mythic 3 are three different fights."""
    return sorted(gr.fights(g), key=lambda f: (f['tier'], f['set'], f['name']))


def slot_name(f):
    return TIER_NAMES[f['tier']] + ' ' + str(f['set'] + 1)


def one(g, fight, debuffs, U, sp, rows, idx, lv, trig, act, gear, tier_key, mow_names):
    """the best five for one boss at one setting"""
    boss, ds, _ = gr.boss_defender(g, fight, debuffs)
    rules = gr.boss_rules(g, fight)
    banned = gr.FACTION_ID.get(fight['faction'], fight['faction'])
    opts = gr.mow_options(g, fight, boss, ds, lv, tier_key, banned, trig)
    # search with the machine that usually wins, then check it against the rest and only search again
    # if a different one suits the five better
    mow = max(opts, key=lambda o: ((o['buff'] or {}).get('pct', 0) if not (o['buff'] or {}).get('only') else 0,
                                   o['own'])) if opts else None
    team, score = gr.best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules, tier_key=tier_key, mow=mow)
    if opts:
        pick = gr.best_mow(team, opts, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None)
        if pick['name'] != mow['name']:
            mow = pick
            team, score = gr.best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules,
                                       tier_key=tier_key, mow=mow)
    score_of = lambda t: gr.team_damage(t, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None, mow)
    buff = mow['buff'] if mow else None
    five = []
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra = gr.outrage(m, team, boss, ds, rows, sp, lv, trig, act, gear) if m['name'] == 'Laviscus' else 0.0
        extra += gr.parasite(m, team, boss, lv, gear, tier_key)
        if buff and buff['kind'] == 'dmg' and sm.matches(m, buff['who']):
            extra += m['dmg'] * buff['pct'] / 100
        alone = gr.member_damage(m, [], boss, ds, rows, sp, lv, trig, act, gear, rules)
        with_team = gr.member_damage(m, mates, boss, ds, rows, sp, lv, trig, act, gear, rules, extra, gr.TURNS, buff)
        five.append([idx[m['name']], round(with_team), round(alone)])
    # who else would fit: the best swap each character outside the five could make
    names = {m['name'] for m in team}
    alts = []
    for u in U:
        if u['name'] in names or u['faction'] == banned:
            continue
        best = max(score_of(team[:i] + [u] + team[i + 1:]) for i in range(gr.TEAM))
        alts.append([idx[u['name']], round(best - score)])
    alts.sort(key=lambda x: -x[1])
    out = dict(s=round(score), f=five, a=alts[:ALTS])
    if mow:
        out['m'] = [mow_names.index(mow['name']), round(mow['own'])] + ([round(buff['pct']), buff['kind']] if buff else [])
    return out


def job(args):
    tier_key, key, lv, trig, act, gear = args
    units, specs = _tier(tier_key)
    g = gr.game()
    idx = {u['name']: i for i, u in enumerate(units)}
    mow_names = [m['name'] for m in gr.machines(g)]
    rows = sm.load_rows('Attack')
    U, sp, _, _ = sm.setting_units(units, specs, lv, trig, act, gear)
    res = []
    for fight in fight_list(g):
        res.append([one(g, fight, d, U, sp, rows, idx, lv, trig, act, gear, tier_key, mow_names) for d in (False, True)])
    return tier_key, key, res


def write_page(data):
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('guild_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page-only', action='store_true', help="rebuild the page from the template with the last build's numbers")
    if ap.parse_args().page_only:
        with open(OUT, encoding='utf-8') as f:
            m = re.search(r'const DATA = (\{.*?\});\n', f.read(), re.S)
        if not m:
            sys.exit('No numbers in guild-raid.html yet: run a full build first.')
        write_page(json.loads(m.group(1)))
        print('Rebuilt guild-raid.html from the template (numbers unchanged).')
        return
    start = time.time()
    g = gr.game()
    fights = fight_list(g)
    jobs, tiers = [], []
    for t in bm.TIERS:
        bm.set_tier(t)
        gd, units = bm.load()
        tiers.append(dict(key=t['key'], label=t['label'], levels=list(t['levels']), about=t['about']))
        for key, trig, lv, act, gear in bm.scenario_keys():
            if lv:
                jobs.append((t['key'], key, lv, trig, act, gear))
    chars = [dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in units]
    mows = [dict(n=m['name'], f=m['factionId'],
                 b=(lambda b: dict(name=b['name'], pct=b['pct'], kind=b['kind'], only=b['only'] or '',
                                   who=b['who'], note=b['note']) if b else None)(gr.mow_buff(g, m, 50, 'mythic', True)))
            for m in gr.machines(g)]
    fl = []
    for f in fights:
        boss, ds, dbf = gr.boss_defender(g, f, False)
        _, _, dbf2 = gr.boss_defender(g, f, True)
        fl.append(dict(n=f['name'], t=f['tier'], l=f['level'], hp=f['hp'], r=f['rarity'], slot=slot_name(f),
                       ban=gr.FACTION_ID.get(f['faction'], f['faction']), arm=round(boss['arm']),
                       bc=round(ds['bc'] * 100), bd=round(ds['bd']),
                       dbf=[round(dbf2['armour']), round(dbf2['block'])],
                       rules=gr.boss_rules(g, f)['notes'],
                       traits=sorted(boss['traits'])))
    data = dict(version=g['version'], tiers=tiers, chars=chars, mows=mows, fights=fl, turns=gr.TURNS,
                r={t['key']: {} for t in tiers})
    with Pool(min(len(jobs), os.cpu_count() or 4)) as pool:
        for tier_key, key, res in pool.imap_unordered(job, jobs):
            data['r'][tier_key][key] = res
            print(f'  {tier_key} {key}  ({time.time() - start:.0f}s)', flush=True)
    write_page(data)
    print(f'Built guild-raid.html: {len(fights)} boss fights x {len(jobs)} settings x 2 (side battles), '
          f'game version {g["version"]}, {time.time() - start:.0f}s.')


if __name__ == '__main__':
    main()
