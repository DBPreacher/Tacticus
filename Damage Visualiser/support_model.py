"""
support_model.py - how much an Attack-side support helps its allies (the planned Support Map).

Reads support_abilities.csv and runs every buff through build_map.py's damage model: for each support
and each ally who can receive the buff, the ally's Damage score (the middle of its 117 matchups) with
and without it. "Boost" = how much faster the ally kills a typical character: k_without / k_with - 1.

Rules (PLAN.md, owner decisions September 2026):
- conditional parts follow the Traits switch (@trig), support actives and 'active' rows the Active switch;
  relics only at Mythic with gear on.
- +Damage buffs work on normal attacks, as a character's own passive does in the map (ability damage
  doesn't use the Damage stat). Enemy debuffs (armour, taken, takenpct) and 'ability' buffs also reach
  the ally's active.
- the support never buffs itself here: its own damage is on the Roster Battle Map.

    python -X utf8 support_model.py            # rankings at the default setting (Diamond III, level 36)
"""
import argparse, copy, csv, os, re, statistics as st, sys
import build_map as bm

HERE = os.path.dirname(os.path.abspath(__file__))
SUPPORT_CSV = os.path.join(HERE, 'support_abilities.csv')
SPACING = {'typical': {'adjacent': 2, '2 hexes': 3}, 'tight': {'adjacent': 3, '2 hexes': 4}, 'spread': {'adjacent': 1, '2 hexes': 2}}
FIXED_REACH = {'team': 4, 'target': 4, 'one': 1, 'next attack': 1}


def parse(tok):
    """'kind:value[:scope][:opt=val...][@trig]' -> dict"""
    trig = tok.endswith('@trig')
    t = tok[:-5] if trig else tok
    parts = t.split(':')
    out = dict(kind=parts[0], arg=parts[1] if len(parts) > 1 else '', scope='all', trig=trig, opts={})
    for p in parts[2:]:
        if '=' in p:
            k, v = p.split('=', 1)
            out['opts'][k] = v
        elif p == 'gearonly':
            out['opts']['gearonly'] = True
        elif p:
            out['scope'] = p
    return out


def matches(u, who):
    """who: 'all', 'has:ranged', 'no:ranged', or names ('|' = or) matched against alliance, faction, traits; '!' = not"""
    if not who or who == 'all':
        return True
    neg = who.startswith('!')
    names = set(who.lstrip('!').split('|'))
    if names & {'has:ranged', 'no:ranged'}:
        has = any(w['kind'] == 'ranged' for w in u['weapons'])
        hit = ('has:ranged' in names and has) or ('no:ranged' in names and not has)
    else:
        hit = bool(names & ({u['alliance'], u['faction']} | u['traits']))
    return hit != neg


def value(ab, var, level, relic=False):
    var = var.strip()
    if re.fullmatch(r'[\d.]+', var):
        return float(var)
    variables, consts = ab.get('variables') or {}, ab.get('constants') or {}
    if var in variables:
        arr = variables[var]
        x = float(str(arr[min((bm.RELIC_LEVEL if relic else level) - 1, len(arr) - 1)]).split(',')[0])
        if not relic and var in (ab.get('variablesAffectedByRarityBonus') or []):
            x *= bm.RARITY_MULT
        return x
    if var in consts:
        return float(consts[var])
    raise KeyError(f"{ab.get('name')}: no variable {var!r}")


def load_rows(side='Attack'):
    """the counted rows of one side ('Attack' or 'Defence')"""
    with open(SUPPORT_CSV, newline='', encoding='utf-8') as f:
        return [r for r in csv.DictReader(f) if r['Effect'].strip() and (r.get('Side') or 'Attack') == side]


def row_ability(U, r):
    u = U[r['Name']]
    if r['Source'] == 'Passive':
        return u['passive'], False
    if r['Source'] == 'Active':
        return u['ability'], False
    return (u['relic'] or {}).get('ability'), True


def tokens_for(r, ally, ab, relic, level, trig):
    """the row's tokens that apply to this ally at this setting, with their values resolved"""
    out = []
    for raw in [t.strip() for t in r['Effect'].split(';') if t.strip()]:
        t = parse(raw)
        if t['trig'] and not trig:
            continue
        o = t['opts']
        if not matches(ally, o.get('who', 'all')):
            continue
        m = re.fullmatch(r'(\d+)x(\w+)\((\w+)(?:-(\w+))?\)', t['arg'])
        if m:
            n, typ, a, b = m.groups()
            lo = value(ab, a, level, relic)
            hi = value(ab, b, level, relic) if b else lo
            t['part'] = dict(dmg=(lo + hi) / 2, hits=int(n), type=bm.dtype(typ), crit=True)
            t['value'] = None
        elif t['kind'] in ('follow', 'reuse'):
            t['value'] = None
        else:
            v = value(ab, o['trig'] if (trig and 'trig' in o) else t['arg'], level, relic)
            if 'mult' in o:
                v *= float(o['mult'])
            if 'trigmult' in o and trig:
                v *= float(o['trigmult'])
            if 'avg' in o and not trig:
                a, b = o['avg'].split('/')
                v *= float(a) / float(b)
            if 'chance' in o:
                v *= 1.0 if trig else value(ab, o['chance'], level, relic) / 100
            t['value'] = v
            if 'cap' in o:
                t['cap'] = value(ab, o['cap'], level, relic)
        out.append(t)
    return out


def _scope(s):
    return {'normal': 'all', 'normal-melee': 'melee', 'normal-ranged': 'ranged'}.get(s, s)


def _vs(o):
    vs = o.get('vs')
    if not vs:
        return None, None
    names = set(vs.lstrip('!').split('|'))
    return (None, names) if vs.startswith('!') else (names, None)


def buffed(ally, toks, spec, gear_on):
    """(ally with the buffs added, active spec with ability-side buffs, armour taken off every enemy)"""
    a = dict(ally)
    ps_eff, ps_desc = (list(a['ps'][0]), list(a['ps'][1])) if a.get('ps') else ([], [])
    pg = list(a.get('pg') or [])
    spec = copy.deepcopy(spec) if spec else None
    armour = 0.0
    for t in toks:
        k, o, v = t['kind'], t['opts'], t.get('value')
        vs, vsnot = _vs(o)
        types = set(o['type'].split('|')) if 'type' in o else None
        notypes = set(o['notype'].split('|')) if 'notype' in o else set()
        scope = _scope(t['scope'])
        weapons = [w for w in a['weapons'] if (scope in ('all', 'ability') or w['kind'] == scope)
                   and (types is None or w['type'] in types) and w['type'] not in notypes]
        # effects on normal attacks, per weapon kind so damage-type filters work
        kinds = sorted({w['kind'] for w in weapons})

        def add(kind, **extra):
            for wk in kinds:
                ps_eff.append(dict(kind=kind, scope=wk, vs=vs, vsnot=vsnot, **extra))
        if scope == 'ability':
            if spec and k == 'pct':
                for p in spec['parts']:
                    p['dmg'] *= 1 + v / 100
            elif spec and k == 'hits' and spec['parts']:
                spec['parts'][0]['hits'] += int(v)
            continue
        if k == 'hits' and 'cap' not in t and v != int(v):
            # a chance of an extra hit (Shadowsun): the expected share of a hit, as extra damage
            for w in weapons:
                ps_eff.append(dict(kind='pct', scope=w['kind'], vs=vs, vsnot=vsnot, value=v / w['hits'] * 100))
        elif k in ('flat', 'pct', 'pierce', 'armignore', 'ramp') or (k == 'hits' and 'cap' not in t):
            add({'flat': 'flat', 'pct': 'pct', 'pierce': 'pierce', 'armignore': 'armignore', 'ramp': 'ramp', 'hits': 'hits'}[k], value=v)
        elif k == 'hits':                              # an extra hit of the ally's own weapon, capped
            for w in weapons:
                part = dict(dmg=min(a['dmg'], t['cap']), hits=int(v), type=w['type'], crit=True)
                ps_eff.append(dict(kind='extra', scope=w['kind'], vs=vs, vsnot=vsnot, part=part))
        elif k in ('extra', 'partner'):
            add('extra', part=t['part'])
        elif k == 'attack':                            # an extra normal attack at a share of the ally's Damage
            w = max(weapons, key=lambda x: x['hits']) if weapons else None
            if w:
                part = dict(dmg=min(a['dmg'] * v / 100, t.get('cap', 1e9)), hits=w['hits'], type=w['type'], crit=True)
                ps_eff.append(dict(kind='extra', scope='all', vs=vs, vsnot=vsnot, part=part))
        elif k == 'follow':
            add('follow')
        elif k in ('taken', 'takenpct'):               # on the enemy: normal attacks and the active
            add('flat' if k == 'taken' else 'pct', value=v)
            if spec and t['scope'] == 'all':
                for p in spec['parts']:
                    if k == 'taken':
                        p['dmg'] += v
                    else:
                        p['dmg'] *= 1 + v / 100
        elif k == 'armour':
            armour += v
        elif k in ('critchance', 'critdmg'):
            if not a.get('g'):
                if o.get('gearonly'):
                    continue
                a['g'] = dict(cc=0.0, cd=0.0, bc=0.0, bd=0.0, hp=0.0, arm=0.0, items=[])
            pg.append(dict(kind=k, value=v / 100 if k == 'critchance' else v, scope=scope if scope != 'all' else 'all', vs=vs, vsnot=vsnot))
        elif k == 'dmgfromblock':
            if a.get('g'):
                pg.append(dict(kind='dmgfromblock', value=v / 100, scope='all', vs=vs, vsnot=vsnot))
        elif k == 'reuse':
            if spec:
                spec['parts'] = spec['parts'] + copy.deepcopy(spec['parts'])
        else:
            sys.exit(f'support_abilities.csv: unknown token kind {k!r}')
    a['ps'] = (ps_eff, ps_desc) if ps_eff else a.get('ps')
    a['pg'] = pg
    return a, spec, armour


def setting_units(units, specs, lv, trig, act, gear):
    """the same per-scenario setup as build_map.run_scenarios"""
    sp = specs[(lv, trig, gear)]
    U = [dict(u, hp=u['hp'] + u['gear']['hp'], arm=u['arm'] + u['gear']['arm'], g=u['gear']) if gear
         else dict(u, g=None) for u in units]
    for u in U:
        u['ps'] = sp['passive'].get(u['name'])
        u['pg'] = sp['passive_goff'].get(u['name'])
    rnd = {u['name']: bm.merge_defence(*((sp['active_def'].get(u['name']), sp['active_gdef'].get(u['name'])) if act else ()),
                                       sp['passive_def'].get(u['name']), sp['passive_gdef'].get(u['name'])) for u in U}
    rest = {u['name']: bm.merge_defence(sp['passive_def'].get(u['name']), sp['passive_gdef'].get(u['name'])) for u in U}
    return U, sp, rnd, rest


def damage_score(a, U, trig, spec, rnd, rest, armour=0.0):
    ks = []
    for d in U:
        if d.get('_skip'):
            continue
        dd = dict(d, arm=max(d['arm'] - armour, 0.0)) if armour else d
        ks.append(bm.attacks_to_kill(a, dd, trig, spec, rnd[d['name']], rest[d['name']])[0])
    return st.median(ks)


def run(units, specs, rows, tier_key, lv, trig, act, gear, only=None):
    """{row index: [(ally name, boost against the enemies it works on, share of the roster those enemies are)]}
    for every support row that counts at this setting and helps at least one ally. summarize() turns it
    into the page's numbers."""
    U, sp, rnd, rest = setting_units(units, specs, lv, trig, act, gear)
    byname = {u['name']: u for u in U}
    UA = {u['name']: u for u in units}
    base = {}
    out = {}
    for ri, r in enumerate(rows):
        if only and r['Name'] not in only:
            continue
        if (r['Source'] == 'Active' or r['Condition'] == 'active') and not act:
            continue
        if r['Condition'] == 'trig' and not trig:
            continue
        if r['Source'] == 'Relic' and not (tier_key == 'mythic' and gear):
            continue
        ab, relic = row_ability(UA, r)
        res = []
        for ally in U:
            if ally['name'] == r['Name'] or not matches(ally, r['Receives']):
                continue
            toks = tokens_for(r, ally, ab, relic, lv, trig)
            if not toks:
                continue
            # a buff that only works against some enemies (Psykers, Daemons, Chaos) is measured against those
            vs_sets = [_vs(tk['opts'])[0] for tk in toks]
            vs = set().union(*vs_sets) if all(vs_sets) else None
            pool = [d if (vs is None or vs & (d['traits'] | {d['alliance']})) else dict(d, _skip=True) for d in U]
            spec = sp['active'].get(ally['name']) if act else None
            a2, spec2, armour = buffed(ally, toks, spec, gear)
            key = (ally['name'], tuple(sorted(vs)) if vs else None)
            if key not in base:
                base[key] = damage_score(ally, pool, trig, spec, rnd, rest)
            k1 = damage_score(a2, pool, trig, spec2, rnd, rest, armour)
            boost = base[key] / k1 - 1
            if boost > 0.005:                          # only allies it actually helps
                share = sum(1 for d in pool if not d.get('_skip')) / len(pool)
                res.append((ally['name'], boost, share))
        if res:
            out[ri] = res
    return out


def summarize(row, allies, spacing='typical'):
    """the page's numbers for one support. A buff that only works against some enemies is scored across
    the whole roster (boost x the share of enemies it works on, owner, September 2026); the team figure
    assumes a team built to use the buff (owner)."""
    per = sorted((b * s for _, b, s in allies), reverse=True)
    boost = st.median(per)
    n = FIXED_REACH.get(row['Reach']) or SPACING[spacing].get(row['Reach'], 1)
    vs_only = any(s < 1 for _, _, s in allies)
    return dict(boost=boost, n=n, team=boost * n, eligible=len(allies),
                vs_boost=st.median(b for _, b, _ in allies) if vs_only else None)


WORDS = {'flat': '+{:,.0f} Damage', 'pct': '+{:.0f}% damage', 'hits': '+{:.0f} hit', 'pierce': '+{:.0f}% pierce',
         'critchance': '+{:.0f}% crit chance', 'critdmg': '+{:,.0f} Crit Damage', 'armignore': 'ignore {:,.0f} Armour',
         'ramp': 'each hit +{:,.0f} more than the last', 'attack': 'an extra attack at {:.0f}% Damage',
         'armour': 'enemy Armour -{:,.0f}', 'taken': 'enemy takes +{:,.0f} Damage a hit',
         'takenpct': 'enemy takes +{:.0f}% damage', 'dmgfromblock': '+{:.0f}% of Block Damage as Damage'}
SCOPES = {'normal': 'normal attacks', 'normal-melee': 'normal melee', 'normal-ranged': 'normal ranged', 'ability': 'actives'}


def _who(x):
    x = x.replace('|', '/')
    return 'not ' + x[1:] if x.startswith('!') else x


def describe(effect, ab, relic, level):
    """a token list in words, with the values at this level (for the page and for checking)"""
    out = []
    for tok in [x.strip() for x in effect.split(';') if x.strip()]:
        tk = parse(tok)
        o = tk['opts']
        m = re.fullmatch(r'(\d+)x(\w+)\((\w+)(?:-(\w+))?\)', tk['arg'])
        if m:
            n, typ, a, b = m.groups()
            lo = value(ab, a, level, relic)
            hi = value(ab, b, level, relic) if b else lo
            s = f'+{n}\u00d7 {typ} {(lo + hi) / 2:,.0f}' + (' on each of their attacks' if tk['kind'] == 'partner' else ' hit')
        elif tk['kind'] in ('follow', 'reuse'):
            s = {'follow': 'a free ranged attack after each melee attack', 'reuse': 'uses their active a second time'}[tk['kind']]
        else:
            v = value(ab, tk['arg'], level, relic) * float(o.get('mult', 1))
            s = WORDS[tk['kind']].format(v)
            if 'trig' in o:
                s += f' (up to {value(ab, o["trig"], level, relic):,.0f})'
            if 'cap' in o:
                s += f' (max {value(ab, o["cap"], level, relic):,.0f} a hit)'
            if 'chance' in o:
                s += f' ({value(ab, o["chance"], level, relic):.0f}% chance a round)'
            if 'avg' in o:
                s += ' (every third round)'
            if 'trigmult' in o:
                s += f' (x{o["trigmult"]} over a battle)'
        bits = []
        if tk['scope'] != 'all':
            bits.append(SCOPES.get(tk['scope'], tk['scope']))
        if 'who' in o:
            bits.append(_who(o['who']))
        if 'vs' in o:
            bits.append('vs ' + _who(o['vs']))
        if 'type' in o:
            bits.append(o['type'].replace('|', '/'))
        if 'notype' in o:
            bits.append('not ' + o['notype'])
        if tk['trig']:
            bits.append('All triggered')
        out.append(s + (f" ({', '.join(bits)})" if bits else ''))
    return '; '.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trig', action='store_true')
    ap.add_argument('--active', action='store_true')
    ap.add_argument('--gear', action='store_true')
    ap.add_argument('--level', type=int, default=36)
    args = ap.parse_args()
    bm.set_tier(bm.TIERS[1])
    g, units = bm.load()
    actives = bm.sync_rows(bm.ACTIVES_CSV, bm.ACTIVE_COLS, 'Active', units, bm.draft_active, 'active_abilities.csv')
    passives = bm.sync_rows(bm.PASSIVES_CSV, bm.PASSIVE_COLS, 'Passive', units, bm.draft_passive, 'passive_abilities.csv')
    relics = bm.sync_relics(g, units)
    specs = bm.build_specs(units, actives, passives, relics)
    rows = load_rows()
    res = run(units, specs, rows, 'd3', args.level, args.trig, args.active, args.gear)
    print(f"Diamond III, abilities {args.level}, {'all triggered' if args.trig else 'always-on'}, "
          f"active {'on' if args.active else 'off'}, {'standard gear' if args.gear else 'no gear'}")
    print(f"{'support':<34}{'per ally':>9}{'reach':>15}{'team':>8}{'can use':>9}  best allies")
    table = sorted(((ri, summarize(rows[ri], al)) for ri, al in res.items()), key=lambda x: -x[1]['team'])
    for ri, x in table:
        r = rows[ri]
        best = ', '.join(f'{n} +{b * s * 100:.0f}%' for n, b, s in sorted(res[ri], key=lambda y: -y[1] * y[2])[:3])
        vs = f" (+{x['vs_boost'] * 100:.0f}% vs the enemies it works on)" if x['vs_boost'] else ''
        print(f"{r['Name'] + ' (' + r['Source'].lower() + ')':<34}{x['boost'] * 100:>8.0f}%{r['Reach'] + ' (' + str(x['n']) + ')':>15}"
              f"{x['team'] * 100:>7.0f}%{x['eligible']:>9}  {best}{vs}")


if __name__ == '__main__':
    main()
