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
        if ally is not None and not matches(ally, o.get('who', 'all')):
            continue      # ally=None: no receiver yet, so the 'who' travels with the token
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
            if 'avg' in o:                            # a cycle (Aun'Shi): a share in both settings (owner)
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


def _tok_order(t):
    """The order buffs land in. Without this a team's damage depends on the order its five happen to be
    listed in, because a token that lifts damage only lifts the parts that already exist when it lands:
    first everything that adds to the character's own attacks, then the ability-scope multipliers on
    those attacks, and last what the enemy takes - which lifts everything it takes."""
    if t['kind'] in ('taken', 'takenpct'):
        # flat first, then the percentages, the way a normal attack does it
        return 2 if t['kind'] == 'taken' else 3
    if _scope(t['scope']) == 'ability':
        return 1
    return 0


def buffed(ally, toks, spec, gear_on):
    """(ally with the buffs added, active spec with ability-side buffs, armour taken off every enemy)"""
    a = dict(ally)
    ps_eff, ps_desc = (list(a['ps'][0]), list(a['ps'][1])) if a.get('ps') else ([], [])
    pg = list(a.get('pg') or [])
    spec = copy.deepcopy(spec) if spec else None
    armour = 0.0
    for t in sorted(toks, key=_tok_order):
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
            if vs or vsnot:
                # No row needs this yet. It would have to hang the condition on the part the way the
                # taken/takenpct branch does, so stop rather than silently apply it to every enemy.
                sys.exit(f"support_abilities.csv: {t['kind']} on an ability scope can't take a vs= yet")
            # "attacks that are not normal attacks": the character's active, and also the extra attack a
            # passive adds (Kariyan's Legacy of Combat, Kharn's second attack). +hits lands on one of them.
            if k == 'pct':
                if spec:
                    for p in spec['parts']:
                        p['dmg'] *= 1 + v / 100
                for i, e in enumerate(ps_eff):
                    if e['kind'] in ('extra', 'extrahalf'):
                        new = dict(e, part=dict(e['part'], dmg=e['part']['dmg'] * (1 + v / 100)))
                        if e.get('part_big'):
                            new['part_big'] = dict(e['part_big'], dmg=e['part_big']['dmg'] * (1 + v / 100))
                        ps_eff[i] = new
            elif k == 'hits':
                if spec and spec['parts']:
                    spec['parts'][0]['hits'] += int(v)
                else:
                    for i, e in enumerate(ps_eff):
                        if e['kind'] in ('extra', 'extrahalf'):
                            new = dict(e, part=dict(e['part'], hits=e['part']['hits'] + int(v)))
                            if e.get('part_big'):
                                new['part_big'] = dict(e['part_big'], hits=e['part_big']['hits'] + int(v))
                            ps_eff[i] = new
                            break
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
        elif k in ('taken', 'takenpct'):               # on the enemy: every kind of damage it takes
            add('flat' if k == 'taken' else 'pct', value=v)
            if t['scope'] == 'all':
                # A buff that only applies to some enemies (Roswitha against Daemons) can't be folded in
                # here, because the enemy isn't known yet: hang the condition on the part and let
                # build_map.mods_for settle it. Everything else is added straight away.
                cond = dict(kind=k, value=v, vs=vs, vsnot=vsnot) if (vs or vsnot) else None
                bump = (lambda x: x + v) if k == 'taken' else (lambda x: x * (1 + v / 100))
                hit = (lambda p: dict(p, mods=list(p.get('mods') or []) + [cond])) if cond                     else (lambda p: dict(p, dmg=bump(p['dmg'])))
                if spec:
                    spec['parts'] = [hit(p) for p in spec['parts']]
                # the hits a passive adds are damage the enemy takes too (Kariyan's Legacy of Combat,
                # Kharn's second attack): copy the part rather than change the cached character
                for i, e in enumerate(ps_eff):
                    if e['kind'] in ('extra', 'extrahalf'):
                        new = dict(e, part=hit(e['part']))
                        if e.get('part_big'):
                            new['part_big'] = hit(e['part_big'])
                        ps_eff[i] = new
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
        u['summons'] = sp['summons'].get(u['name'])
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


# ---------------------------------------------------------------- Defence side
ROUND_ONLY = ('1 round', 'until his next turn', 'until their next turn', '2 rounds', 'once')


def dvalue(sup, ab, var, level, relic=False):
    """a Defence value: 'healaction' = the support's Damage x their most hits (Healer / Mechanic trait),
    'a-b' = the middle of two variables, else a game variable (value())"""
    if var == 'healaction':
        return sup['dmg'] * max(w['hits'] for w in sup['weapons'])
    if '-' in var:
        a, b = var.split('-')
        return (dvalue(sup, ab, a, level, relic) + dvalue(sup, ab, b, level, relic)) / 2
    return value(ab or {}, var, level, relic)


def defence_for(r, sup, ally, ab, relic, level, trig):
    """(ds for the first enemy turn, ds for later turns, regen dict, attacker filter) from one Defence row.
    Actives and short effects only cover the first enemy turn, like defensive actives on the roster map."""
    first, later, regen = bm.new_ds(), bm.new_ds(), dict(turn=0.0, hit=0.0, shield=0.0, shield_first=0.0)
    round_only = r['Source'] == 'Active' or r['Lasts'] in ROUND_ONLY
    scopes, vs_list, any_tok = [], [], False
    for raw in [x.strip() for x in r['Effect'].split(';') if x.strip()]:
        tk = parse(raw)
        if tk['trig'] and not trig:
            continue
        o = tk['opts']
        if not matches(ally, o.get('who', 'all')):
            continue
        any_tok = True
        k, arg = tk['kind'], tk['arg']
        scope = tk['scope']
        vs = set(o['vs'].split('|')) if 'vs' in o else None
        scopes.append(scope)
        vs_list.append(vs)
        mult = 1.0
        if 'avg' in o:
            a_, b_ = o['avg'].split('/')
            mult *= float(a_) / float(b_)
        if 'chance' in o:
            mult *= dvalue(sup, ab, o['chance'], level, relic) / 100
        v = lambda x: dvalue(sup, ab, x, level, relic) * mult
        targets = [first] if round_only else [first, later]
        if k == 'suppress':
            for ds in targets:
                ds['enemy'].append((bm.SUPPRESSED, arg or 'all', vs))
        elif k == 'pct':
            for ds in targets:
                ds['pct'].append((1 - min(v(arg), 95) / 100, scope, vs))
        elif k == 'epct':
            for ds in targets:
                ds['enemy'].append((1 - min(v(arg), 95) / 100, scope, vs))
        elif k == 'flat':
            for ds in targets:
                ds['flat'].append((v(arg), scope, vs))
        elif k == 'hitsless':
            for ds in targets:
                ds['hitsless'].append((v(arg), scope, vs))
        elif k == 'pctcap':
            pv, cv = arg.split('/')
            for ds in targets:
                ds['pctcap'].append((v(pv) / 100, dvalue(sup, ab, cv, level, relic), scope, vs))
        elif k == 'armour':
            for ds in targets:
                ds['armour'] += v(arg)
        elif k == 'armourpass':
            for ds in targets:
                ds['pass2'] += v(arg)
        elif k == 'blockchance':
            for ds in targets:
                ds['bc'] += v(arg) / 100
        elif k == 'blockdmg':
            for ds in targets:
                ds['bd'] += v(arg)
        elif k in ('heal', 'revive'):
            first['heal'] += v(arg)
        elif k == 'revivepct':
            first['heal'] += ally['hp'] * v(arg) / 100
        elif k == 'healdmg':
            m = re.fullmatch(r'(\w+)\((\w+)-(\w+)\)', arg)
            first['heal'] += v(m.group(1)) / 100 * dvalue(sup, ab, m.group(2) + '-' + m.group(3), level, relic)
        elif k == 'setpct':
            first['hpmult'] *= v(arg) / 100
        elif k == 'regen':
            regen['turn'] += v(arg)
        elif k == 'regenhit':
            regen['hit'] += v(arg)
        elif k == 'shield':
            regen['shield_first' if round_only else 'shield'] += v(arg)
        else:
            sys.exit(f'support_abilities.csv: unknown Defence token kind {k!r}')
        first['text'].append(k); later['text'].append(k)
    if not any_tok:
        return None
    # a buff that only works against some attackers (Psychic ones, or Chaos) is measured against those
    if scopes and all(x == 'psychic' for x in scopes):
        attackers = ('psychic', None)
    elif vs_list and all(vs_list):
        attackers = ('vs', set().union(*vs_list))
    else:
        attackers = (None, None)
    return first, later, (regen if any(regen.values()) else None), attackers


FOCUS = {'focused': 5, 'spread': 2}      # enemy attacks on one ally per enemy turn (owner: a switch, Focused first)
HORIZON_TURNS = 10                       # stop counting after 10 enemy turns: "survives 10+ turns" (owner)


def toughness_score(ally, U, trig, act, specs_active, rnd, rest, regen=None, pool=None):
    """(the middle attacks-to-kill over the attackers, whether that reached the 10-turn horizon)"""
    cap = HORIZON_TURNS * bm.ATTACKS_PER_TURN
    reg = dict(regen or {}, limit=cap)          # the counting stops at the horizon (fast, and the same answer)
    ks = []
    for a in (pool or U):
        spec = specs_active.get(a['name']) if act else None
        ks.append(min(bm.attacks_to_kill(a, ally, trig, spec, rnd, rest, reg)[0], cap))
    m = st.median(ks)
    return m, m >= cap - 1e-9


def run_defence(units, specs, rows, tier_key, lv, trig, act, gear, only=None):
    """{row index: [(ally, protection against the attackers it works on, share of the roster they are)]}.
    Protection = how many more attacks a typical enemy needs to kill the ally: k_with / k_without - 1.
    Unlike the Attack side, allies it makes easier to kill are kept (Nicodemus's Blood Chalice)."""
    U, sp, rnd, rest = setting_units(units, specs, lv, trig, act, gear)
    UA = {u['name']: u for u in units}
    SU = {u['name']: u for u in U}
    base, out = {}, {}
    for ri, r in enumerate(rows):
        if only and r['Name'] not in only:
            continue
        if (r['Source'] == 'Active' or r['Condition'] == 'active') and not act:
            continue
        if r['Condition'] == 'trig' and not trig:
            continue
        if r['Source'] == 'Relic' and not (tier_key == 'mythic' and gear):
            continue
        ab, relic = (None, False) if r['Source'] == 'Trait' else row_ability(UA, r)
        sup = SU[r['Name']]
        res = []
        for ally in U:
            if ally['name'] == r['Name'] or not matches(ally, r['Receives']):
                continue
            got = defence_for(r, sup, ally, ab, relic, lv, trig)
            if not got:
                continue
            ds1, ds2, regen, (flt, vs) = got
            if flt == 'psychic':
                pool = [a for a in U if any(w['type'] in ('Psychic', 'Direct') for w in a['weapons'])]
            elif flt == 'vs':
                pool = [a for a in U if vs & (a['traits'] | {a['alliance']})]
            else:
                pool = None
            key = (ally['name'], flt, tuple(sorted(vs)) if vs else None)
            if key not in base:
                base[key] = toughness_score(ally, U, trig, act, sp['active'], rnd[ally['name']], rest[ally['name']], None, pool)[0]
            r1 = bm.merge_defence(rnd[ally['name']], ds1)
            r2 = bm.merge_defence(rest[ally['name']], ds2)
            k1, capped = toughness_score(ally, U, trig, act, sp['active'], r1, r2, regen, pool)
            boost = k1 / base[key] - 1
            if abs(boost) > 0.005:
                res.append((ally['name'], boost, (len(pool) / len(U)) if pool else 1.0, capped))
        if res:
            out[ri] = res
    return out


def summarize(row, allies, spacing='typical'):
    """the page's numbers for one support. A buff that only works against some enemies is scored across
    the whole roster (boost x the share of enemies it works on, owner, September 2026); the team figure
    assumes a team built to use the buff (owner)."""
    per = sorted((x[1] * x[2] for x in allies), reverse=True)
    boost = st.median(per)
    n = FIXED_REACH.get(row['Reach']) or SPACING[spacing].get(row['Reach'], 1)
    vs_only = any(x[2] < 1 for x in allies)
    return dict(boost=boost, n=n, team=boost * n, eligible=len(allies),
                vs_boost=st.median(x[1] for x in allies) if vs_only else None)


WORDS = {'flat': '+{:,.0f} Damage', 'pct': '+{:.0f}% damage', 'hits': '+{:.0f} hit', 'pierce': '+{:.0f}% pierce',
         'critchance': '+{:.0f}% crit chance', 'critdmg': '+{:,.0f} Crit Damage', 'armignore': 'ignore {:,.0f} Armour',
         'ramp': 'each hit +{:,.0f} more than the last', 'attack': 'an extra attack at {:.0f}% Damage',
         'armour': 'enemy Armour -{:,.0f}', 'taken': 'enemy takes +{:,.0f} Damage a hit',
         'takenpct': 'enemy takes +{:.0f}% damage', 'dmgfromblock': '+{:.0f}% of Block Damage as Damage'}
SCOPES = {'normal': 'normal attacks', 'normal-melee': 'normal melee', 'normal-ranged': 'normal ranged', 'ability': 'actives'}


DWORDS = {'heal': '+{:,.0f} health once', 'regen': '+{:,.0f} health every turn', 'regenhit': '+{:,.0f} health after each attack',
          'shield': 'a {:,.0f} shield', 'revive': 'back with {:,.0f} health once', 'revivepct': '{:.0f}% of their health back once',
          'pct': '-{:.0f}% damage taken', 'epct': 'enemies deal -{:.0f}% damage', 'flat': '-{:,.0f} damage a hit',
          'hitsless': 'attackers score -{:.0f} hit', 'armour': '+{:,.0f} Armour', 'armourpass': 'attacks go through {:,.0f} Armour again',
          'blockchance': '+{:.0f}% block chance', 'blockdmg': '+{:,.0f} Block Damage', 'setpct': 'set to {:.0f}% health'}
DSCOPES = {'melee': 'from melee', 'ranged': 'from ranged', 'one': 'first attack each turn', 'psychic': 'from Psychic'}


def describe_defence(effect, sup, ab, relic, level):
    """a Defence token list in words, with the values at this level"""
    out = []
    for tok in [x.strip() for x in effect.split(';') if x.strip()]:
        tk = parse(tok)
        o, k, arg = tk['opts'], tk['kind'], tk['arg']
        if k == 'suppress':
            s = 'suppresses ' + ('one enemy' if arg == 'one' else 'the enemies around')
        elif k == 'pctcap':
            a, b = arg.split('/')
            s = f'-{dvalue(sup, ab, a, level, relic):.0f}% damage taken (max -{dvalue(sup, ab, b, level, relic):,.0f} a hit)'
        elif k == 'healdmg':
            m = re.fullmatch(r'(\w+)\((\w+)-(\w+)\)', arg)
            s = f'+{dvalue(sup, ab, m.group(1), level, relic) / 100 * dvalue(sup, ab, m.group(2) + "-" + m.group(3), level, relic):,.0f} health once'
        else:
            v = dvalue(sup, ab, arg, level, relic)
            if 'chance' in o:
                v *= dvalue(sup, ab, o['chance'], level, relic) / 100
            s = DWORDS[k].format(v)
            if 'avg' in o:
                s += ' (every third round)'
        bits = [DSCOPES.get(tk['scope'], tk['scope'])] if tk['scope'] != 'all' else []
        if 'who' in o:
            bits.append(_who(o['who']))
        if 'vs' in o:
            bits.append('vs ' + _who(o['vs']))
        if tk['trig']:
            bits.append('All triggered')
        out.append(s + (f" ({', '.join(bits)})" if bits else ''))
    return '; '.join(out)


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
    ap.add_argument('--defence', action='store_true', help='the Defence side')
    ap.add_argument('--spread', action='store_true', help='Defence: enemies spread their attacks (2 a turn on one ally)')
    args = ap.parse_args()
    bm.ATTACKS_PER_TURN = FOCUS['spread' if args.spread else 'focused']
    bm.set_tier(bm.TIERS[1])
    g, units = bm.load()
    actives = bm.sync_rows(bm.ACTIVES_CSV, bm.ACTIVE_COLS, 'Active', units, bm.draft_active, 'active_abilities.csv')
    passives = bm.sync_rows(bm.PASSIVES_CSV, bm.PASSIVE_COLS, 'Passive', units, bm.draft_passive, 'passive_abilities.csv')
    relics = bm.sync_relics(g, units)
    specs = bm.build_specs(units, actives, passives, relics)
    rows = load_rows('Defence' if args.defence else 'Attack')
    res = (run_defence if args.defence else run)(units, specs, rows, 'd3', args.level, args.trig, args.active, args.gear)
    print('DEFENCE side' if args.defence else 'ATTACK side')
    print(f"Diamond III, abilities {args.level}, {'all triggered' if args.trig else 'always-on'}, "
          f"active {'on' if args.active else 'off'}, {'standard gear' if args.gear else 'no gear'}")
    print(f"{'support':<34}{'per ally':>9}{'reach':>15}{'team':>8}{'can use':>9}  best allies")
    table = sorted(((ri, summarize(rows[ri], al)) for ri, al in res.items()), key=lambda x: -x[1]['team'])
    for ri, x in table:
        r = rows[ri]
        best = ', '.join(f'{y[0]} {y[1] * y[2] * 100:+.0f}%' + (' (10+ turns)' if len(y) > 3 and y[3] else '')
                         for y in sorted(res[ri], key=lambda y: -y[1] * y[2])[:3])
        vs = f" (+{x['vs_boost'] * 100:.0f}% vs the enemies it works on)" if x['vs_boost'] else ''
        print(f"{r['Name'] + ' (' + r['Source'].lower() + ')':<34}{x['boost'] * 100:>8.0f}%{r['Reach'] + ' (' + str(x['n']) + ')':>15}"
              f"{x['team'] * 100:>7.0f}%{x['eligible']:>9}  {best}{vs}")


if __name__ == '__main__':
    main()
