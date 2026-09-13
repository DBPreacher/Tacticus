#!/usr/bin/env python3
"""Build the Roster Battle Map from the cached game data.

    python -X utf8 update_game_data.py      # first, if there has been a patch
    python -X utf8 build_map.py             # then this
    python -X utf8 build_map.py --creed "C:/path/Tacticus - Castellan Creed Test.csv"   # plus the Creed check

Steps:
  1. Reads the roster from ../LRE Script/tacticus_characters.csv (MoW and Do_Not_Use rows skipped)
     and every character's stats, weapons, traits and active ability from cache/gameinfo.json.
  2. Adds a draft row to active_abilities.csv for any character that doesn't have one yet.
     Rows already there are never changed, except the Active and Ability_Text columns. If the
     ability text has changed since the last run, the row is flagged Needs_Review=Y.
  3. Works out Damage and Toughness for six scenarios: traits always-on / all triggered, each
     with no active ability, or opening with it at ability level 36 or 50 (ABILITY_LEVELS).
     Rules are in DAMAGE_MODEL.md.
  4. Writes ../LRE Script/tacticus_stats.csv and roster-battle-map.html.
See INSTRUCTIONS.md.
"""
import argparse, csv, json, os, re, statistics as st, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache', 'gameinfo.json')
ROSTER_CSV = os.path.join(ROOT, 'LRE Script', 'tacticus_characters.csv')
STATS_CSV = os.path.join(ROOT, 'LRE Script', 'tacticus_stats.csv')
ACTIVES_CSV = os.path.join(HERE, 'active_abilities.csv')
TEMPLATE = os.path.join(HERE, 'map_template.html')
OUT_HTML = os.path.join(HERE, 'roster-battle-map.html')

# ---- Standard setup (DAMAGE_MODEL.md "Standard setup") ----
RANK = 'DIAMOND III'
STARS = 11                      # Winged = the Legendary star = 11 stars
STAR_MULT = 1 + 0.1 * STARS     # rank stats in the game data are at 0 stars
ABILITY_LEVELS = (36, 50)        # the 'with active' views; 36 = the video standard, 50 = Legendary cap
RARITY_MULT = 1.8               # Legendary. Common 1.0, +0.2 per rarity step, Mythic 2.0

PIERCE = {'Bio': .30, 'Blast': .15, 'Bolter': .20, 'Chain': .20, 'Direct': 1, 'Energy': .30,
          'Eviscerating': .50, 'Flame': .25, 'Heavy Round': .55, 'Las': .10, 'Melta': .75,
          'Molecular': .60, 'Particle': .35, 'Physical': .01, 'Piercing': .80, 'Plasma': .65,
          'Power': .40, 'Projectile': .15, 'Psychic': 1, 'Pulse': .20, 'Toxic': .70}
TYPE_NAMES = {'Eviscerate': 'Eviscerating', 'Gauss': 'Molecular', 'HeavyRound': 'Heavy Round',
              'DirectDamage': 'Direct'}
# CSV name -> game data name, where the normalised names don't match
ALIAS = {'commandershadowsun': 'shadowsun', 'commanderfarsight': 'farsight', 'nauseousrotbone': 'rotbone'}

COUNTED = {'TerminatorArmour', 'MkXGravis', 'Parry', 'Terrifying', 'MartialKatah', 'Camouflage', 'BeastSlayer'}
SITUATIONAL = {'RapidAssault', 'HeavyWeapon', 'CrushingStrike', 'RangedSpecialist', 'PrioritisedEfficiency',
               'ContagionsOfNurgle', 'WeaverOfFate', 'BlessingsOfKhorne', 'ShadowInTheWarp', 'Daemon',
               'GetStuckIn', 'LetTheGalaxyBurn'}

ACTIVE_COLS = ['Name', 'Active', 'Kind', 'Damage_Parts', 'Normal_Attack', 'Normal_Bonus', 'Same_Turn',
               'Defence', 'Needs_Review', 'Notes', 'Ability_Text']
SUPPRESSED, STUNNED = 0.7, 0.5      # damage multipliers of a Suppressed / Stunned enemy (wiki)


def norm(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'")).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', s.lower())


def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def dtype(name):
    return TYPE_NAMES.get(name, name)


# ---------------------------------------------------------------- data loading
def load():
    if not os.path.exists(CACHE):
        sys.exit('No cache/gameinfo.json yet: run update_game_data.py first.')
    with open(CACHE, encoding='utf-8') as f:
        g = json.load(f)
    g = g.get('data', g)
    by_norm = {}
    for h in g['heroes'].values():
        for k in (h['longName'], h['name'], h['id']):
            by_norm.setdefault(norm(k), h)
    with open(ROSTER_CSV, newline='', encoding='utf-8') as f:
        roster = [r for r in csv.DictReader(f) if r['Is_MoW'] == 'N' and r['Do_Not_Use'] == 'N']
    units, missing = [], []
    for r in roster:
        h = by_norm.get(norm(r['Name'])) or by_norm.get(ALIAS.get(norm(r['Name']), '#'))
        if not h:
            missing.append(r['Name'])
            continue
        rk = next(x for x in h['ranks'] if x['level'] == RANK)

        def weapon(w, kind):
            if not w:
                return None
            return dict(kind=kind, type=dtype(w['damageProfile']), hits=w['hits'],
                        pierce=w['piercingRatio'] / 100, range=w.get('range') or 1)
        units.append(dict(name=r['Name'], faction=r['Faction'], alliance=r['Alliance'],
                          hp=rk['health'] * STAR_MULT, dmg=rk['damage'] * STAR_MULT, arm=rk['armor'] * STAR_MULT,
                          weapons=[w for w in (weapon(h['meleeWeapon'], 'melee'),
                                               weapon(h.get('rangeWeapon'), 'ranged')) if w],
                          traits=set(h['traits'] or []),
                          ability=g['abilities'].get(h.get('activeAbility') or '')))
    if missing:
        print('WARNING - in the CSV but not in the game data (add to ALIAS?):', ', '.join(missing))
    return g, units


# ---------------------------------------------------------------- active abilities
def ability_value(ab, key, level):
    """value of an ability variable at an ability level and the standard rarity"""
    v = (ab.get('variables') or {}).get(key)
    if v is None:
        v = (ab.get('constants') or {}).get(key)
        return float(v) if v not in (None, '') and re.match(r'^-?\d+(\.\d+)?$', str(v)) else None
    raw = float(v[level - 1] if isinstance(v, list) else v)
    return raw * RARITY_MULT if key in (ab.get('variablesAffectedByRarityBonus') or []) else raw


def part_suffix(p):
    return '' if p == '1' else '_' + p


def draft_active(u):
    """best-guess row for a character's active ability; the owner reviews it"""
    ab = u['ability'] or {}
    v = ab.get('variables') or {}
    raw = ab.get('description') or ''
    txt = clean(raw)
    low = txt.lower()
    parts = [p for p in ('1', '2', '3') if f'minDmg{part_suffix(p)}' in v and f'maxDmg{part_suffix(p)}' in v]
    normal = re.search(r'perform\w* (a |an )?normal (melee |ranged )?attack', low)
    pct = 'dmgPct' in v and normal
    bonus = 'dmg' if ('dmg' in v and '{[dmg]}' in raw and normal) else ''
    same_turn = 'Y' if 'does not end' in low else 'N'
    if parts or normal:
        kind = 'damage'
    elif 'summon' in low:
        kind = 'summon'
    elif re.search(r'\bheal|repair', low):
        kind = 'heal'
    elif re.search(r'block|shield|damage reduction|receive -|take -|takes -', low):
        kind = 'defence'
    else:
        kind = 'support'
    flags = [w for w in ('for each', 'if ', 'instead', 'behind', 'additional enemy', 'up to', 'possess',
                         'summon', 'rest of the battle', 'all adjacent') if w in low]
    defence = []
    if '-{[dmgreductionpct]}% damage' in low: defence.append('pct:dmgReductionPct')
    if '-{[dmgreduction]} damage' in low: defence.append('flat:dmgReduction')
    if re.search(r'(heals|repairs) (himself|herself|itself)', low): defence.append('heal:hpToHeal')
    if 'suppress' in low: defence.append('suppress:one')
    if 'stun' in low: defence.append('stun:one')
    review = 'Y' if ((kind == 'damage' and (flags or len(parts) > 1)) or defence) else 'N'
    notes = ('Check: ' + ', '.join(repr(f) for f in flags)) if review == 'Y' and flags else ''
    if defence:
        notes = (notes + ' Check the Defence guess.').strip()
    return dict(Name=u['name'], Active=ab.get('name', ''), Kind=kind, Damage_Parts=';'.join(parts),
                Normal_Attack='PCT' if pct else ('Y' if normal else 'N'), Normal_Bonus=bonus,
                Same_Turn=same_turn, Defence=';'.join(defence), Needs_Review=review, Notes=notes, Ability_Text=txt)


def sync_actives(units):
    rows = {}
    if os.path.exists(ACTIVES_CSV):
        with open(ACTIVES_CSV, newline='', encoding='utf-8') as f:
            rows = {r['Name']: r for r in csv.DictReader(f)}
    added, changed = [], []
    for u in units:
        d = draft_active(u)
        if u['name'] not in rows:
            rows[u['name']] = d
            added.append(u['name'])
            continue
        r = rows[u['name']]
        if r.get('Ability_Text') != d['Ability_Text']:
            r['Needs_Review'] = 'Y'
            r['Notes'] = ('Ability text changed; ' + r.get('Notes', '')).strip()
            changed.append(u['name'])
        r['Active'], r['Ability_Text'] = d['Active'], d['Ability_Text']
    with open(ACTIVES_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=ACTIVE_COLS)
        w.writeheader()
        for name in sorted(rows):
            w.writerow({k: rows[name].get(k, '') for k in ACTIVE_COLS})
    if added:
        print(f'active_abilities.csv: drafted {len(added)} new row(s): {", ".join(added)}')
    if changed:
        print(f'active_abilities.csv: ability text changed, now flagged for review: {", ".join(changed)}')
    review = [n for n, r in rows.items() if r['Needs_Review'] == 'Y']
    if review:
        print(f'active_abilities.csv: {len(review)} row(s) marked Needs_Review=Y: {", ".join(sorted(review))}')
    return rows


def part_hits(ab, text, s, dmg_key, level):
    """hit count for one damage part, read from the text in front of its damage value:
    '{[nrOfHits_2]}x {[minDmg]}' (Calgar), '6x {[minDmg]}' (Imospekh), else nrOfHits{s}"""
    m = re.search(r'(?:\{\[(\w+)\]\}|(\d+))\s*x\s*\{\[' + re.escape(dmg_key) + r'\]\}', text)
    if m and m.group(2):
        return int(m.group(2))
    key = m.group(1) if m else f'nrOfHits{s}'
    return int(ability_value(ab, key, level) or ability_value(ab, 'nrOfHits', level) or 1)


def active_spec(u, row, level):
    """turn a reviewed row into numbers the model can use.
    Damage_Parts tokens: 1 / 2 / 3 = the minDmg/maxDmg pair with that suffix;
    key[i] = entry i of a comma-separated flat-damage variable (Aethana's dmg[0]).
    Normal_Bonus: a variable name = that many extra hits of flat damage on the normal attack
    (Pestillian's dmg); +key = add that variable to the Damage stat for the normal attack."""
    ab = u['ability'] or {}
    if not row or row['Kind'] != 'damage':
        return None
    consts = ab.get('constants') or {}
    text = row['Ability_Text']
    parts = []
    for tok in filter(None, (t.strip() for t in row['Damage_Parts'].split(';'))):
        flat = re.match(r'(\w+)\[(\d+)\]$', tok)
        if flat:
            key, i = flat.groups()
            vals = (ab.get('variables') or {})[key][level - 1].split(',')
            dmg = float(vals[int(i)]) * (RARITY_MULT if key in (ab.get('variablesAffectedByRarityBonus') or []) else 1)
            hits = int(ability_value(ab, 'nrOfHits', level) or 1)
            prof = consts.get('damageProfile') or 'Physical'
        else:
            s = part_suffix(tok)
            lo, hi = ability_value(ab, f'minDmg{s}', level), ability_value(ab, f'maxDmg{s}', level)
            dmg = (lo + hi) / 2
            hits = part_hits(ab, text, s, f'minDmg{s}', level)
            prof = consts.get(f'damageProfile{s}') or consts.get('damageProfile') or 'Physical'
        parts.append(dict(dmg=dmg, hits=hits, type=dtype(prof)))
    low = text.lower()
    spec = dict(parts=parts, normal=row['Normal_Attack'], same_turn=row['Same_Turn'] == 'Y',
                weapon='melee' if 'normal melee attack' in low else ('ranged' if 'normal ranged attack' in low else None))
    if row['Normal_Attack'] == 'PCT':
        spec['pct'] = (ability_value(ab, 'dmgPct', level) or 100) / 100
        spec['cap'] = ability_value(ab, 'maxDmg', level)
    bonus = row['Normal_Bonus'].strip()
    if bonus.startswith('+'):
        spec['flat'] = ability_value(ab, bonus[1:], level) or 0
    elif bonus:
        spec['bonus'] = dict(dmg=ability_value(ab, bonus, level), hits=int(ability_value(ab, 'nrOfHits', level) or 1),
                             type=dtype(consts.get('damageProfile') or 'Physical'))
    return spec


def describe_active(spec):
    if not spec:
        return ''
    bits = [f"{p['hits']}× {p['type']} {p['dmg']:,.0f}" for p in spec['parts']]
    extra = ''
    if spec.get('bonus'):
        extra = f" with +{spec['bonus']['hits']}× {spec['bonus']['type']} {spec['bonus']['dmg']:,.0f}"
    elif spec.get('flat'):
        extra = f" with +{spec['flat']:,.0f} Damage"
    if spec['normal'] == 'Y':
        bits.append('a normal attack' + extra)
        extra = ''
    elif spec['normal'] == 'PCT':
        bits.append(f"a normal attack at {spec['pct'] * 100:.0f}% Damage (max {spec['cap']:,.0f} a hit)")
    if spec['same_turn']:
        bits.append('a normal attack the same turn' + extra)
    return ' + '.join(bits)


# ---------------------------------------------------------------- damage model
def hit_value(D, A, p, gravis):
    y = max(D - A, D * p)
    if gravis and p < 1:
        y = max(y - A, y * p)
    return y


def normal_attack(a, d, w, trig, dmg_override=None):
    """one normal attack: (damage, ignores Terminator Armour). See DAMAGE_MODEL.md."""
    at, dt = a['traits'], d['traits']
    n, p = w['hits'], w['pierce']
    D, A = (dmg_override if dmg_override is not None else a['dmg']), d['arm']
    psychic = w['type'] in ('Psychic', 'Direct')
    melee = w['kind'] == 'melee'
    if melee and 'Parry' in dt and n > 1:
        n -= 1
    if not melee and 'Camouflage' in dt:
        n = max(1, n - (2 if (trig and w['range'] >= 3) else 1))
    if trig:
        if 'GetStuckIn' in at: n += (n // 2) * 0.3
        if 'LetTheGalaxyBurn' in at: n += 0.33
        if 'WeaverOfFate' in at: D *= 1.2
        if 'ContagionsOfNurgle' in at and melee: A *= 0.8
    y = hit_value(D, A, p, 'MkXGravis' in dt)
    m = 1.0
    if melee and 'Terrifying' in dt: m *= 0.7
    if 'MartialKatah' in dt: m *= 0.8
    if melee and 'BeastSlayer' in at and ({'BigTarget', 'Vehicle'} & dt): m *= 1.2
    if w['type'] == 'Melta' and 'Vehicle' in dt: m *= 1.5
    if trig:
        if 'RapidAssault' in at: m *= 1.25
        if not melee and 'HeavyWeapon' in at: m *= 1.25
        if melee and 'CrushingStrike' in at: m *= 1.5
        if not melee and 'RangedSpecialist' in at: m *= 1.33
        if 'PrioritisedEfficiency' in at: m *= 1.25
        if 'BlessingsOfKhorne' in at: m *= 1.12              # 4 of 8 stacks
        if 'PrioritisedEfficiency' in dt: m *= 0.75
        if psychic and 'BlessingsOfKhorne' in dt: m *= 0.68
        if psychic and 'ShadowInTheWarp' in dt and 'Psyker' in at: m *= 0.75
    per_hit = y * m
    total = per_hit * n
    if trig and not psychic:
        # random blocks: the chain starts on hit 1, each later hit re-rolls until one fails
        for chance, block in (((0.25, 0.5 * d['dmg']) if 'Daemon' in dt else (0, 0)),
                              ((0.10, d['arm']) if 'BeastSlayer' in dt else (0, 0))):
            if chance:
                total -= sum(chance ** k for k in range(1, int(n) + 1)) * min(block, per_hit)
    return max(total, 1.0), psychic


def best_normal(a, d, trig, kind=None, dmg_override=None):
    best = None
    for w in a['weapons']:
        if kind and w['kind'] != kind:
            continue
        dmg, psy = normal_attack(a, d, w, trig, dmg_override)
        if best is None or dmg > best[0]:
            best = (dmg, psy, w['kind'])
    if best is None:                      # asked for a weapon it doesn't have
        return best_normal(a, d, trig, None, dmg_override)
    return best


def ability_hits(part, d):
    """ability damage: armour, pierce and Mk X Gravis only (abilities aren't 'normal attacks')"""
    p = PIERCE.get(part['type'], .2)
    return hit_value(part['dmg'], d['arm'], p, 'MkXGravis' in d['traits']) * part['hits'], part['type'] in ('Psychic', 'Direct')


def opener(a, d, trig, spec):
    """damage of the turn the character uses its active ability, as a list of attacks in order"""
    attacks = [ability_hits(p, d) for p in spec['parts']]
    bonus_used = False

    def normal_with_bonus(kind, override):
        nonlocal bonus_used
        if spec.get('flat') and not bonus_used:
            override = (override if override is not None else a['dmg']) + spec['flat']
        dmg, psy, _ = best_normal(a, d, trig, kind, override)
        if spec.get('bonus') and not bonus_used:
            dmg += ability_hits(spec['bonus'], d)[0]
        bonus_used = True
        return dmg, psy
    if spec['normal'] in ('Y', 'PCT'):
        override = min(a['dmg'] * spec['pct'], spec['cap'] or 1e9) if spec['normal'] == 'PCT' else None
        attacks.append(normal_with_bonus(spec['weapon'], override))
    if spec['same_turn']:
        attacks.append(normal_with_bonus(spec['weapon'], None))
    return attacks


def kill_count(first_turn, normal, d, hp=None):
    """attacks to kill; first_turn is a list of (damage, ignores_TA) dealt in the first turn"""
    ta = 'TerminatorArmour' in d['traits']
    opening = 0
    for i, (dmg, psy) in enumerate(first_turn):
        opening += dmg * (0.25 if (ta and i == 0 and not psy) else 1)
    hp = d['hp'] if hp is None else hp
    if opening >= hp:
        return hp / opening
    return 1 + (hp - opening) / max(normal, 1.0)


def _prod(vals):
    out = 1.0
    for v in vals:
        out *= v
    return out


def _scoped(items, kind):
    """values of (value, scope) pairs that apply to an attack of this kind"""
    return [v for v, sc in items if sc in ('all', kind)]


def normal_vs_defence(a, d, w, trig, ds):
    """one normal attack against a defender using a defensive active:
    (damage of every attack, damage of the first attack only, ignores TA)"""
    flat = sum(_scoped(ds['flat'], w['kind']))
    flat_one = sum(v for v, sc in ds['flat'] if sc == 'one')
    dmg, psy = normal_attack(a, d, w, trig, max(a['dmg'] - flat, 0) if flat else None)
    first = normal_attack(a, d, w, trig, max(a['dmg'] - flat - flat_one, 0))[0] if flat_one else dmg
    m = _prod(_scoped(ds['pct'], w['kind'])) * _prod(_scoped(ds['enemy'], w['kind']))
    m1 = _prod(v for v, sc in ds['enemy'] if sc == 'one')
    return dmg * m, first * m * m1, psy


def attacks_to_kill(a, d, trig, spec, ds=None):
    """(attacks, best attack kind, normal attack damage, used the active).
    spec = the attacker's active (offence), ds = the defender's active (defence)."""
    if not ds:
        dmg, psy, kind = best_normal(a, d, trig)
        k = kill_count([(dmg, psy)], dmg, d)
        if spec:
            k_act = kill_count(opener(a, d, trig, spec), dmg, d)
            if k_act < k:
                return k_act, kind, dmg, True
        return k, kind, dmg, False
    hp = d['hp'] * ds['hpmult'] + ds['heal']
    best = None
    for w in a['weapons']:
        dmg, first, psy = normal_vs_defence(a, d, w, trig, ds)
        if best is None or dmg > best[0]:
            best = (dmg, first, psy, w['kind'])
    dmg, first, psy, kind = best
    k = kill_count([(first, psy)], dmg, d, hp)
    used = False
    if spec:
        # ability damage: only the defender's effects that cover every attack apply (no melee/ranged scope)
        m_all = _prod(v for v, sc in ds['pct'] if sc == 'all') * _prod(v for v, sc in ds['enemy'] if sc == 'all')
        m1 = _prod(v for v, sc in ds['enemy'] if sc == 'one')
        op = [(x * m_all * (m1 if i == 0 else 1), p) for i, (x, p) in enumerate(opener(a, d, trig, spec))]
        k_act = kill_count(op, dmg, d, hp)
        if k_act < k:
            k, used = k_act, True
    return k, kind, dmg, used


def defence_spec(u, row, level):
    """parse a row's Defence tokens (see INSTRUCTIONS.md) into numbers the model can use"""
    toks = [t.strip() for t in (row or {}).get('Defence', '').split(';') if t.strip()]
    if not toks:
        return None
    ab = u['ability'] or {}

    def val(expr):
        return sum(ability_value(ab, k, level) or 0 for k in expr.split('+'))
    ds = dict(pct=[], flat=[], enemy=[], heal=0.0, hpmult=1.0, text=[])
    where = {'all': '', 'ranged': ' from ranged attacks', 'melee': ' from melee attacks', 'one': ' from one enemy'}
    for t in toks:
        p = t.split(':')
        kind, arg = p[0], (p[1] if len(p) > 1 else '')
        if kind in ('suppress', 'stun'):
            scope = arg or 'all'
            ds['enemy'].append((SUPPRESSED if kind == 'suppress' else STUNNED, scope))
            who = {'one': 'one enemy', 'melee': 'adjacent enemies'}.get(scope, 'nearby enemies')
            ds['text'].append(('suppresses ' if kind == 'suppress' else 'stuns ') + who)
        elif kind in ('pct', 'epct', 'flat'):
            v, scope = val(arg), (p[2] if len(p) > 2 else 'all')
            if kind == 'pct':
                v = min(v, 95)
                ds['pct'].append((1 - v / 100, scope))
                ds['text'].append(f'takes -{v:.0f}% damage{where[scope]}')
            elif kind == 'epct':
                v = min(v, 95)
                ds['enemy'].append((1 - v / 100, scope))
                ds['text'].append(f"{'adjacent enemies' if scope == 'melee' else 'enemies'} deal -{v:.0f}% damage")
            else:
                ds['flat'].append((v, scope))
                ds['text'].append(f'takes -{v:,.0f} damage per hit{where[scope]}')
        elif kind == 'heal':
            v = val(arg)
            ds['heal'] += v
            ds['text'].append(f'+{v:,.0f} health')
        elif kind == 'lose':
            v = val(arg)
            ds['hpmult'] *= 1 - v / 100
            ds['text'].append(f'loses {v:.0f}% of its health')
        elif kind == 'setpct':
            v = val(arg)
            ds['hpmult'] *= v / 100
            ds['text'].append(f'drops to {v:.0f}% health')
        else:
            sys.exit(f"{u['name']}: unknown Defence token {t!r} in active_abilities.csv")
    return ds


def describe_defence(ds):
    return '; '.join(ds['text']) if ds else ''


def scenario_keys():
    keys = [('base', False, None), ('trig', True, None)]
    for lv in ABILITY_LEVELS:
        keys += [(f'base_a{lv}', False, lv), (f'trig_a{lv}', True, lv)]
    return keys


def run_scenarios(units, specs, dspecs):
    """specs[level][name] -> offence spec, dspecs[level][name] -> defence spec.
    Scenario keys: base, trig, base_a36, trig_a36, ..."""
    out = {}
    for key, trig, lv in scenario_keys():
        K = {a['name']: {d['name']: attacks_to_kill(a, d, trig, specs[lv].get(a['name']) if lv else None,
                                                    dspecs[lv].get(d['name']) if lv else None) for d in units}
             for a in units}
        dmg = {a: st.median(v[0] for v in K[a].values()) for a in K}
        tough = {d['name']: st.median(K[a['name']][d['name']][0] for a in units) for d in units}
        kinds = {a: max(('melee', 'ranged'), key=lambda k: sum(1 for v in K[a].values() if v[1] == k)) for a in K}
        rd = {n: i + 1 for i, n in enumerate(sorted(dmg, key=dmg.get))}
        rt = {n: i + 1 for i, n in enumerate(sorted(tough, key=tough.get, reverse=True))}
        out[key] = {n: dict(d=round(dmg[n], 3), t=round(tough[n], 3), rd=rd[n], rt=rt[n], k=kinds[n]) for n in dmg}
        if key == 'base':
            out['creed'] = {n: dict(to=round(K[n]['Castellan Creed'][2]), frm=round(K['Castellan Creed'][n][2]),
                                    kill=round(K[n]['Castellan Creed'][0], 2), die=round(K['Castellan Creed'][n][0], 2))
                            for n in dmg}
    return out


# ---------------------------------------------------------------- outputs
def pretty(t):
    s = re.sub(r'(?<!^)(?=[A-Z])', ' ', t).replace(' Of ', ' of ').replace(' The ', ' the ')
    return {'Martial Katah': "Martial Ka'tah", 'Weaver of Fate': 'Weaver of Fates', 'Mk X Gravis': 'Mk X Gravis'}.get(s, s)


def write_stats(units, res, actives, specs, dspecs, version):
    cols = ['Name', 'Faction', 'Alliance', 'Health', 'Damage', 'Armour',
            'Melee_Type', 'Melee_Hits', 'Melee_Pierce', 'Ranged_Type', 'Ranged_Hits', 'Ranged_Pierce', 'Ranged_Range',
            'Active_Ability', 'Active_Kind']
    cols += [f'Active_Counted_L{lv}' for lv in ABILITY_LEVELS] + [f'Active_Defence_L{lv}' for lv in ABILITY_LEVELS]
    cols += [f'Damage_{k}' for k, _, _ in scenario_keys()] + [f'Toughness_{k}' for k, _, _ in scenario_keys()]
    cols += ['Game_Version']
    with open(STATS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for u in sorted(units, key=lambda u: u['name']):
            wp = {x['kind']: x for x in u['weapons']}
            m, r = wp.get('melee'), wp.get('ranged')
            n = u['name']
            w.writerow([n, u['faction'], u['alliance'], round(u['hp']), round(u['dmg']), round(u['arm']),
                        m['type'] if m else '', m['hits'] if m else '', f"{m['pierce']:.0%}" if m else '',
                        r['type'] if r else '', r['hits'] if r else '', f"{r['pierce']:.0%}" if r else '', r['range'] if r else '',
                        actives[n]['Active'], actives[n]['Kind'], *[describe_active(specs[lv].get(n)) for lv in ABILITY_LEVELS],
                        *[describe_defence(dspecs[lv].get(n)) for lv in ABILITY_LEVELS],
                        *[f"{res[k][n]['d']:.2f}" for k, _, _ in scenario_keys()],
                        *[f"{res[k][n]['t']:.2f}" for k, _, _ in scenario_keys()],
                        version])


def write_html(units, res, actives, specs, dspecs, version):
    chars = []
    for u in units:
        n = u['name']
        row = actives.get(n, {})
        chars.append(dict(name=n, faction=u['faction'], alliance=u['alliance'],
                          hp=round(u['hp']), dmg=round(u['dmg']), arm=round(u['arm']),
                          weapons=[f"{w['kind'].title()}: {w['type']} ×{w['hits']}" for w in u['weapons']],
                          counted=sorted(pretty(t) for t in u['traits'] & COUNTED),
                          situational=sorted(pretty(t) for t in u['traits'] & SITUATIONAL),
                          active=dict(name=row.get('Active', ''), kind=row.get('Kind', ''), notes=row.get('Notes', ''),
                                      counted={lv: describe_active(specs[lv].get(n)) for lv in ABILITY_LEVELS},
                                      defence={lv: describe_defence(dspecs[lv].get(n)) for lv in ABILITY_LEVELS},
                                      review=row.get('Needs_Review') == 'Y'),
                          s={k: res[k][n] for k, _, _ in scenario_keys()},
                          creed=res['creed'][n]))
    data = dict(version=version, levels=list(ABILITY_LEVELS), chars=chars)
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('map_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False)))


def creed_check(path, units):
    """compare against the owner's Creed test numbers. Those numbers include Rapid Assault and
    Ranged Specialist (the game shows them), so this check adds them back."""
    U = {norm(u['name']): u for u in units}
    creed = U[norm('Castellan Creed')]

    def game_like(a, d, w):
        dmg, _ = normal_attack(a, d, w, False)
        if 'TerminatorArmour' in d['traits'] and w['type'] not in ('Psychic', 'Direct'):
            dmg *= 0.25
        if 'RapidAssault' in a['traits']: dmg *= 1.25
        if w['kind'] == 'ranged' and 'RangedSpecialist' in a['traits']: dmg *= 1.33
        return dmg
    ok = tot = 0
    with open(path, encoding='utf-8') as f:
        rows = list(csv.reader(f))[1:]
    for r in rows:
        u = U.get(norm(r[1]))
        if not u:
            continue
        for kind, val, att, dfn in (('melee', r[2], u, creed), ('ranged', r[3], u, creed), ('melee', r[4], creed, u)):
            w = next((x for x in att['weapons'] if x['kind'] == kind), None)
            if not w or not val or float(val) == 0:
                continue
            tot += 1
            ok += abs(game_like(att, dfn, w) - float(val)) / float(val) <= 0.01
    print(f'Creed check: {ok} of {tot} Creed test numbers within 1% (September 2026 baseline: 148 of 250).')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--creed', help='path to the Castellan Creed test CSV, to re-check the model')
    args = ap.parse_args()
    g, units = load()
    actives = sync_actives(units)
    specs, dspecs = {None: {}}, {None: {}}
    for lv in ABILITY_LEVELS:
        specs[lv] = {u['name']: sp for u in units if (sp := active_spec(u, actives.get(u['name']), lv))}
        dspecs[lv] = {u['name']: ds for u in units if (ds := defence_spec(u, actives.get(u['name']), lv))}
    res = run_scenarios(units, specs, dspecs)
    write_stats(units, res, actives, specs, dspecs, g['version'])
    write_html(units, res, actives, specs, dspecs, g['version'])
    print(f'Built roster-battle-map.html and tacticus_stats.csv: {len(units)} characters, game version {g["version"]}.')
    if args.creed:
        creed_check(args.creed, units)


if __name__ == '__main__':
    main()
