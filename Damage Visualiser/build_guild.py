"""
build_guild.py - builds guild-raid.html, the Guild Raid page ("the best five for this boss").

Runs guild_raid.py's search for every boss and every switch combination (the same tiers and scenarios as
the Roster Battle Map, with the side battles on and off), in parallel, and writes the page from
guild_template.html. Run it after build_map.py:

    python -X utf8 build_guild.py
    python -X utf8 build_guild.py --page-only   # design changes: reuse the last build's numbers
    python -X utf8 build_guild.py --settings mythic:trig_l60_a_g   # one setting, about a minute

A full build is 81 boss fights x 48 settings x side battles x high ground, so about half an hour.
While a change to the model is being checked, build the one setting the videos use and look at that;
do the full build once, at the end.

See INSTRUCTIONS.md ("Guild Raid").
"""
import argparse, csv, json, os, re, sys, time
from multiprocessing import Pool
import build_map as bm
import calc_data
import support_model as sm
import guild_raid as gr

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'guild_template.html')
OUT = os.path.join(HERE, 'guild-raid.html')
CALC_JS = os.path.join(HERE, 'calc.js')
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
    """the boss fights the page covers, in the game's own order. A tier holds several sets, and the game
    names them the way players do: Mythic 1, Mythic 2, Mythic 3 are three different fights.

    Mythic only. The lower tiers are the same bosses with less health, and nobody taking a raid seriously
    is looking at them - guild_raid.py will still score them on the command line."""
    return sorted((f for f in gr.fights(g) if f['tier'] == MYTHIC), key=lambda f: (f['tier'], f['set'], f['name']))


def slot_name(f):
    return TIER_NAMES[f['tier']] + ' ' + str(f['set'] + 1)


def season_names(g):
    """{season id: the boss it finishes on} - a season's last Mythic fight is the one players name it after"""
    return {f['season']: f['name'] for f in gr.fights(g) if f['tier'] == 5 and f['set'] == 2}


def one(g, fight, debuffs, U, sp, rows, idx, lv, trig, act, gear, tier_key, mow_names, high=False, seed=None):
    """the best five for one boss at one setting"""
    boss, ds, dbf = gr.boss_defender(g, fight, debuffs)
    rules = gr.boss_rules(g, fight, dbf if debuffs else None)
    banned = gr.FACTION_ID.get(fight['faction'], fight['faction'])
    opts = gr.mow_options(g, fight, boss, ds, lv, tier_key, banned, trig)
    # search with the machine that usually wins, then check it against the rest and only search again
    # if a different one suits the five better
    mow = max(opts, key=lambda o: ((o['buff'] or {}).get('pct', 0) if not (o['buff'] or {}).get('only') else 0,
                                   o['own'])) if opts else None
    team, score = gr.best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules, tier_key=tier_key,
                               mow=mow, high=high, seed=seed)
    if opts:
        pick = gr.best_mow(team, opts, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None)
        if pick['name'] != mow['name']:
            mow = pick
            team, score = gr.best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules,
                                       tier_key=tier_key, mow=mow, high=high, seed=team)
    score_of = lambda t: gr.team_damage(t, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None, mow, high)
    buff = mow['buff'] if mow else None
    uses = sorted(x for u in team for x in (gr.active_turns(u, gr.FIGHTING) if act else ()))
    extras = {m['name']: gr.member_extra(m, team, boss, ds, rows, sp, lv, trig, act, gear, tier_key, buff)
              for m in team}
    plain = {m['name']: gr.member_damage(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp, lv,
                                         trig, act, gear, rules, extras[m['name']], gr.FIGHTING, buff, uses)
             for m in team}
    on_high = gr.high_ground(plain) if high else set()
    if on_high:                               # Outrage grows when its feeders are on the high ground
        for m in team:
            if m['name'] == 'Laviscus':
                extras[m['name']] = gr.member_extra(m, team, boss, ds, rows, sp, lv, trig, act, gear,
                                                    tier_key, buff, on_high)
    five = []
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra = extras[m['name']]
        alone = gr.member_damage(m, [], boss, ds, rows, sp, lv, trig, act, gear, rules)
        with_team = gr.member_damage(m, mates, boss, ds, rows, sp, lv, trig, act, gear, rules, extra, gr.FIGHTING,
                                     buff, uses, m['name'] in on_high)
        five.append([idx[m['name']], round(with_team), round(alone)] + ([1] if m['name'] in on_high else []))
    # who else would fit: the best swap each character outside the five could make
    names = {m['name'] for m in team}
    # a character who would improve the five almost always does it by replacing its weakest member, so
    # trying that one slot gives the same list for a fifth of the work
    weak = min(range(gr.TEAM), key=lambda i: plain.get(team[i]['name'], 0.0))
    alts = []
    for u in U:
        if u['name'] in names or u['faction'] == banned:
            continue
        alts.append([idx[u['name']], round(score_of(team[:weak] + [u] + team[weak + 1:]) - score)])
    alts.sort(key=lambda x: -x[1])
    out = dict(s=round(score), f=five, a=alts[:ALTS])
    if mow:
        out['m'] = [mow_names.index(mow['name']), round(mow['own'])] + ([round(buff['pct']), buff['kind']] if buff else [])
    return out


MYTHIC = 5                     # the game's tier number for a Mythic fight

# The one setting the page is built at (owner, September 2026). It used to build all sixteen - level 50
# and 60, gear on and off, triggers on and off, actives on and off - times 81 fights times the side
# battles times the high ground: 5,184 answers, which is why the search had to be shallow enough to run
# 5,184 times. This is the setting the videos are recorded at, and everything else is still available from
# guild_raid.py on the command line. 14 answers can be searched properly instead.
SETTING = dict(tier='mythic', key='trig_l60_a_g', lv=60, trig=True, act=True, gear=True, dbf=True, high=True)


def job(lo):
    """the answer for one fight, at the setting the page is built at"""
    units, specs = _tier(SETTING['tier'])
    g = gr.game()
    idx = {u['name']: i for i, u in enumerate(units)}
    mow_names = [m['name'] for m in gr.machines(g)]
    key_u = tuple(SETTING[k] for k in ('tier', 'lv', 'trig', 'act', 'gear'))
    if key_u not in _cache:                   # the roster at this setting, once per worker
        _cache[key_u] = (sm.load_rows('Attack'),) + sm.setting_units(
            units, specs, SETTING['lv'], SETTING['trig'], SETTING['act'], SETTING['gear'])[:2]
    rows, U, sp = _cache[key_u]
    got = one(g, fight_list(g)[lo], SETTING['dbf'], U, sp, rows, idx, SETTING['lv'], SETTING['trig'],
              SETTING['act'], SETTING['gear'], SETTING['tier'], mow_names, SETTING['high'])
    return lo, got


def write_page(data):
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    for ph in ('/*DATA*/', '/*CALC*/', '/*CALCJS*/'):
        if ph not in html:
            sys.exit(f'guild_template.html is missing its {ph} placeholder.')
    g = gr.game()
    # the Calculate button: calc.js runs the model in the browser, calc_data.py hands it the numbers
    with open(CALC_JS, encoding='utf-8') as f:
        js = '(function(){' + chr(10) + f.read() + chr(10) + '})();'
    dump = lambda x: json.dumps(x, ensure_ascii=False, separators=(',', ':'))
    html = html.replace('/*CALCJS*/', js).replace('/*CALC*/', dump(calc_data.build(g, fight_list(g))))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', dump(data)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page-only', action='store_true',
                    help="rebuild the page from the template with the last build's numbers")
    args = ap.parse_args()
    if args.page_only:
        with open(OUT, encoding='utf-8') as f:
            m = re.search(r'const DATA = (\{.*?\});' + chr(10), f.read(), re.S)
        if not m:
            sys.exit('No numbers in guild-raid.html yet: run a full build first.')
        write_page(json.loads(m.group(1)))
        print('Rebuilt guild-raid.html from the template (numbers unchanged).')
        return
    start = time.time()
    g = gr.game()
    fights = fight_list(g)
    tier = next(x for x in bm.TIERS if x['key'] == SETTING['tier'])
    bm.set_tier(tier)
    gd, units = bm.load()
    chars = [dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in units]
    mows = [dict(n=m['name'], f=m['factionId'], trig=bool((gr.MOW_BUFF.get(m['name']) or {}).get('trig')),
                 b=(lambda b: dict(name=b['name'], pct=b['pct'], kind=b['kind'], only=b['only'] or '',
                                   who=b['who'], note=b['note']) if b else None)(gr.mow_buff(g, m, 50, 'mythic', True)))
            for m in gr.machines(g)]
    seasons = season_names(g)
    fl = []
    for f in fights:
        boss, ds, _ = gr.boss_defender(g, f, False)
        _, ds2, dbf2 = gr.boss_defender(g, f, True)
        fl.append(dict(n=f['name'], t=f['tier'], l=f['level'], hp=f['hp'], r=f['rarity'], slot=slot_name(f),
                       season=seasons.get(f['season'], f['season']),
                       ban=gr.FACTION_ID.get(f['faction'], f['faction']),
                       arm=round(boss['arm']), bc=round(ds['bc'] * 100), bd=round(ds['bd']),
                       arm2=round(boss['arm'] * (1 - dbf2['armour'] / 100)),
                       bc2=round(max(ds['bc'] * 100 - dbf2['block'], 0)),
                       rules=gr.boss_rules(g, f, dbf2)['notes'], traits=sorted(boss['traits'])))
    data = dict(version=g['version'], chars=chars, mows=mows, fights=fl, turns=gr.TURNS,
                fighting=gr.FIGHTING, high=dict(n=gr.HIGH_GROUND, pct=gr.HIGH_GROUND_PCT),
                about=tier['about'],
                setup=[tier['label'], f"Abilities {SETTING['lv']}", 'Standard gear', 'All triggered',
                       'Actives on', 'Side battles cleared', f'{gr.HIGH_GROUND} on high ground'],
                r=[None] * len(fights))
    with Pool(min(len(fights), os.cpu_count() or 4)) as pool:
        for lo, got in pool.imap_unordered(job, range(len(fights))):
            data['r'][lo] = got
    write_page(data)
    print(f"Built guild-raid.html: {len(fights)} Mythic boss fights at {', '.join(data['setup'])}, "
          f"game version {g['version']}, {time.time() - start:.0f}s.")


if __name__ == '__main__':
    main()
