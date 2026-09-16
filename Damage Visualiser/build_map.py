#!/usr/bin/env python3
"""Build the Roster Battle Map from the cached game data.

    python -X utf8 update_game_data.py      # first, if there has been a patch
    python -X utf8 build_map.py             # then this
    python -X utf8 build_map.py --creed "C:/path/Tacticus - Castellan Creed Test.csv"   # plus the Creed check

Steps:
  1. Reads the roster from ../LRE Script/tacticus_characters.csv (MoW and Do_Not_Use rows skipped)
     and every character's stats, weapons, traits and abilities from cache/gameinfo.json.
  2. Adds a draft row to active_abilities.csv / passive_abilities.csv for any character that
     doesn't have one yet. Rows already there are never changed, except the ability name and
     Ability_Text columns. If the ability text has changed, the row is flagged Needs_Review=Y.
  3. Works out Damage and Toughness for every scenario: traits always-on / all triggered x
     ability level (ABILITY_LEVELS) x active ability off / on. Passives are always on. The plain
     stat line ('base': no abilities, always-on traits) is kept as the reference.
     Rules are in DAMAGE_MODEL.md; the token formats are in INSTRUCTIONS.md.
  4. Writes ../LRE Script/tacticus_stats.csv, roster-battle-map.html and typical-character.html
     (every matchup table, for the "what is a typical character?" graphic).
See INSTRUCTIONS.md.
"""
import argparse, csv, json, os, re, statistics as st, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache', 'gameinfo.json')
ROSTER_CSV = os.path.join(ROOT, 'LRE Script', 'tacticus_characters.csv')
STATS_CSV = os.path.join(ROOT, 'LRE Script', 'tacticus_stats.csv')
ACTIVES_CSV = os.path.join(HERE, 'active_abilities.csv')
PASSIVES_CSV = os.path.join(HERE, 'passive_abilities.csv')
RELICS_CSV = os.path.join(HERE, 'relic_abilities.csv')
RELIC_OWNERS_CSV = os.path.join(HERE, 'relic_owners.csv')
TEMPLATE = os.path.join(HERE, 'map_template.html')
OUT_HTML = os.path.join(HERE, 'roster-battle-map.html')
TYPICAL_TEMPLATE = os.path.join(HERE, 'typical_template.html')
OUT_TYPICAL = os.path.join(HERE, 'typical-character.html')   # the "what is a typical character?" graphic

# ---- Progression tiers (DAMAGE_MODEL.md "Standard setup"). set_tier() applies one. ----
# rank: the rank row in the game data (MYTHIC I/II = Adamantine I/II). stars: rank stats are stored at
# 0 stars and each star adds 10%. rarity: ability multiplier (Common 1.0, +0.2 per step, Mythic 2.0).
# levels: the two Ability level buttons. gear: rarity of standard gear (each item at its top level).
TIERS = [
    dict(key='gold', label='Gold', rank='GOLD I', stars=8, rarity=1.6, levels=(26, 35), gear='Epic', relics=False,
         about='Epic, 8 stars, Gold I'),
    dict(key='d3', label='Diamond III', rank='DIAMOND III', stars=11, rarity=1.8, levels=(36, 50), gear='Legendary',
         relics=False, about='Legendary, Winged (11 stars), Diamond III'),
    dict(key='mythic', label='Mythic', rank='MYTHIC II', stars=14, rarity=2.0, levels=(50, 60), gear='Mythic',
         relics=True, about='Mythic, 14 stars, Adamantine II, relic at level 10'),
]
RELIC_LEVEL = 10                # relic effects: max level. Relic values have no rarity multiplier


def set_tier(t):
    global TIER, RANK, STARS, STAR_MULT, RARITY_MULT, ABILITY_LEVELS, GEAR_RARITY, RELICS, STANDARD
    TIER = t
    RANK, STARS, RARITY_MULT, ABILITY_LEVELS = t['rank'], t['stars'], t['rarity'], t['levels']
    STAR_MULT = 1 + 0.1 * STARS
    GEAR_RARITY, RELICS = t['gear'], t['relics']
    STANDARD = f'base_l{ABILITY_LEVELS[0]}'     # the scenario the Creed sparring line uses


set_tier(TIERS[1])

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
               'Defence', 'Gear', 'Needs_Review', 'Notes', 'Ability_Text']
PASSIVE_COLS = ['Name', 'Passive', 'Attack', 'Defence', 'Gear', 'Needs_Review', 'Notes', 'Ability_Text']
RELIC_COLS = ['Relic', 'Owners', 'Attack', 'Defence', 'Gear', 'Needs_Review', 'Notes', 'Ability_Text']
SUPPRESSED, STUNNED = 0.7, 0.5      # damage multipliers of a Suppressed / Stunned enemy (wiki)
ATTACKS_PER_TURN = 5                # one enemy turn = a full team of 5 attacking (owner, September 2026)


def norm(s):
    s = unicodedata.normalize('NFKD', s.replace('’', "'")).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', s.lower())


def clean(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


def dtype(name):
    return TYPE_NAMES.get(name, name)


def _prod(vals):
    out = 1.0
    for v in vals:
        out *= v
    return out


# ---------------------------------------------------------------- data loading
def standard_gear(h, items, relic=None):
    """the character's standard loadout: for each of its item slots, the best GEAR_RARITY item it may
    equip, at the item's top level. Crit/block items: the highest chance (keeps chains going across hits).
    Defensive items: the most Health + 2 x Armour. Relics are never used."""
    def allowed(v):
        return ((not v.get('allowedFactions') or h['factionId'] in v['allowedFactions'])
                and (not v.get('allowedUnits') or h['id'] in v['allowedUnits']))
    pool = [v for v in items.values() if v.get('rarity') == GEAR_RARITY and not v.get('isUniqueRelic')
            and not v.get('abilityId') and allowed(v)]
    relic_slot = None
    if RELICS and relic:
        # the relic takes one of the character's slots: the same type, or else the nearest kind
        # (Aethana's Phoenix Gem is a block booster but her booster slot is a crit booster)
        near = {'I_Crit': ['I_Crit'], 'I_Block': ['I_Block', 'I_Defensive'], 'I_Defensive': ['I_Defensive', 'I_Block'],
                'I_Booster_Block': ['I_Booster_Block', 'I_Booster_Crit'],
                'I_Booster_Crit': ['I_Booster_Crit', 'I_Booster_Block']}.get(relic['item']['itemType'], [])
        relic_slot = next((t for t in near if t in (h.get('itemSlots') or [])), None)
    gear = dict(cc=0.0, cd=0.0, bc=0.0, bd=0.0, hp=0.0, arm=0.0, items=[])
    crit_chances, crit_bonus = [], 0.0
    for slot in h.get('itemSlots') or []:
        cands = [v for v in pool if v['itemType'] == slot]
        if not cands:
            continue
        top = lambda v: v['levels'][-1]['stats']
        key = {'I_Crit': lambda v: (top(v).get('critChance', 0), top(v).get('critDmg', 0)),
               'I_Block': lambda v: (top(v).get('blockChance', 0), top(v).get('blockDmg', 0)),
               'I_Defensive': lambda v: top(v).get('hp', 0) + 2 * top(v).get('fixedArmor', 0)}.get(
            slot, lambda v: (top(v).get('critChanceBonus', 0) + top(v).get('blockChanceBonus', 0)))
        v = max(cands, key=key)
        if slot == relic_slot:
            v, relic_slot = relic['item'], None           # the relic takes this slot
        st_ = top(v)
        if slot == 'I_Crit':
            crit_chances.append(st_.get('critChance', 0) / 100)
            gear['cd'] += st_.get('critDmg', 0)
            label = f"{st_.get('critChance', 0)}% crit, {st_.get('critDmg', 0):,} Crit Damage"
        elif slot == 'I_Block':
            gear['bc'] += st_.get('blockChance', 0) / 100
            gear['bd'] += st_.get('blockDmg', 0)
            label = f"{st_.get('blockChance', 0)}% block, {st_.get('blockDmg', 0):,} Block Damage"
        elif slot == 'I_Defensive':
            gear['hp'] += st_.get('hp', 0)
            gear['arm'] += st_.get('fixedArmor', 0)
            label = ' '.join(x for x in (f"+{st_['hp']:,} Health" if st_.get('hp') else '',
                                         f"+{st_['fixedArmor']:,} Armour" if st_.get('fixedArmor') else '') if x)
        elif slot == 'I_Booster_Crit':
            crit_bonus += st_.get('critChanceBonus', 0) / 100
            gear['cd'] += st_.get('critDmgBonus', 0)
            label = f"+{st_.get('critChanceBonus', 0)}% crit, +{st_.get('critDmgBonus', 0):,} Crit Damage"
        else:
            gear['bc'] += st_.get('blockChanceBonus', 0) / 100
            gear['bd'] += st_.get('blockDmgBonus', 0)
            label = f"+{st_.get('blockChanceBonus', 0)}% block, +{st_.get('blockDmgBonus', 0):,} Block Damage"
        gear['items'].append(f"{v['name']} ({label}){' · relic' if v.get('abilityId') else ''}")
    # two crit items (e.g. Calandis): 1 - (1-c1)(1-c2), then the booster is added (wiki HDTW_TwoCrit)
    gear['cc'] = (1 - _prod(1 - c for c in crit_chances) if crit_chances else 0.0) + crit_bonus
    gear['bc'] = min(gear['bc'], 1.0)
    return gear


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
    relic_items = {norm(v['name']): v for v in g['items'].values() if v.get('abilityId')}
    owners = {}
    if os.path.exists(RELIC_OWNERS_CSV):
        with open(RELIC_OWNERS_CSV, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                owners[norm(r['Character'])] = r['Relic']
    units, missing = [], []
    for r in roster:
        h = by_norm.get(norm(r['Name'])) or by_norm.get(ALIAS.get(norm(r['Name']), '#'))
        if not h:
            missing.append(r['Name'])
            continue
        rk = next(x for x in h['ranks'] if x['level'] == RANK)
        rname = owners.get(norm(r['Name'])) or owners.get(norm(h['longName']))
        ritem = relic_items.get(norm(rname)) if rname else None
        relic = dict(name=ritem['name'], item=ritem, ability=g['abilities'].get(ritem['abilityId'])) if ritem else None

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
                          ability=g['abilities'].get(h.get('activeAbility') or ''),
                          passive=g['abilities'].get(h.get('passiveAbility') or ''),
                          relic=relic, gear=standard_gear(h, g['items'], relic), ps=None, pg=None, g=None))
    if missing:
        print('WARNING - in the CSV but not in the game data (add to ALIAS?):', ', '.join(missing))
    return g, units


# ---------------------------------------------------------------- ability values
def ability_value(ab, key, level):
    """value of an ability variable at an ability level and the standard rarity"""
    if re.match(r'^-?\d+(\.\d+)?$', key or ''):
        return float(key)                                   # a literal number in a token
    v = (ab.get('variables') or {}).get(key)
    if v is None:
        v = (ab.get('constants') or {}).get(key)
        return float(v) if v not in (None, '') and re.match(r'^-?\d+(\.\d+)?$', str(v)) else None
    raw = float(v[level - 1] if isinstance(v, list) else v)
    return raw * RARITY_MULT if key in (ab.get('variablesAffectedByRarityBonus') or []) else raw


def value_of(ab, expr, level):
    """'a+b' adds variables together"""
    return sum(ability_value(ab, k, level) or 0 for k in expr.split('+'))


def part_suffix(p):
    return '' if p == '1' else '_' + p


def part_hits(ab, text, s, dmg_key, level):
    """hit count for one damage part, read from the text in front of its damage value:
    '{[nrOfHits_2]}x {[minDmg]}' (Calgar), '6x {[minDmg]}' (Imospekh), else nrOfHits{s}"""
    m = re.search(r'(?:\{\[(\w+)\]\}|(\d+))\s*x\s*\{\[' + re.escape(dmg_key) + r'\]\}', text)
    if m and m.group(2):
        return int(m.group(2))
    key = m.group(1) if m else f'nrOfHits{s}'
    return int(ability_value(ab, key, level) or ability_value(ab, 'nrOfHits', level) or 1)


def build_part(ab, text, tok, level):
    """one damage part: '1' / '2' / '3' = the minDmg/maxDmg pair with that suffix;
    'key[i]' = entry i of a comma-separated flat-damage variable (Aethana's dmg[0])"""
    consts = ab.get('constants') or {}
    flat = re.match(r'(\w+)\[(\d+)\]$', tok)
    if flat:
        key, i = flat.groups()
        vals = (ab.get('variables') or {})[key][level - 1].split(',')
        dmg = float(vals[int(i)]) * (RARITY_MULT if key in (ab.get('variablesAffectedByRarityBonus') or []) else 1)
        return dict(dmg=dmg, hits=int(ability_value(ab, 'nrOfHits', level) or 1),
                    type=dtype(consts.get('damageProfile') or 'Physical'), crit='cannot crit' not in text.lower())
    s = part_suffix(tok)
    lo, hi = ability_value(ab, f'minDmg{s}', level), ability_value(ab, f'maxDmg{s}', level)
    if lo is None or hi is None:
        raise ValueError(f'no minDmg{s}/maxDmg{s} in {ab.get("name")}')
    return dict(dmg=(lo + hi) / 2, hits=part_hits(ab, text, s, f'minDmg{s}', level),
                type=dtype(consts.get(f'damageProfile{s}') or consts.get('damageProfile') or 'Physical'),
                crit='cannot crit' not in text.lower())


def part_text(p):
    return f"{p['hits']}× {p['type']} {p['dmg']:,.0f}"


# ---------------------------------------------------------------- review files
def draft_defence(low):
    defence = []
    if '-{[dmgreductionpct]}% damage' in low: defence.append('pct:dmgReductionPct')
    if '-{[dmgreduction]} damage' in low: defence.append('flat:dmgReduction')
    if re.search(r'(heals|repairs|regenerates) (himself|herself|itself)', low): defence.append('heal:hpToHeal')
    if 'suppress' in low: defence.append('suppress:one')
    if 'stun' in low: defence.append('stun:one')
    return defence


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
                         'summon', 'rest of the battle', 'all adjacent', 'overwatch') if w in low]
    defence = draft_defence(low)
    review = 'Y' if ((kind == 'damage' and (flags or len(parts) > 1)) or defence or 'overwatch' in low) else 'N'
    notes = ('Check: ' + ', '.join(repr(f) for f in flags)) if review == 'Y' and flags else ''
    if defence:
        notes = (notes + ' Check the Defence guess.').strip()
    return dict(Name=u['name'], Active=ab.get('name', ''), Kind=kind, Damage_Parts=';'.join(parts),
                Normal_Attack='PCT' if pct else ('Y' if normal else 'N'), Normal_Bonus=bonus,
                Same_Turn=same_turn, Defence=';'.join(defence), Needs_Review=review, Notes=notes, Ability_Text=txt)


def draft_passive(u):
    """best-guess row for a character's passive ability; the owner reviews it"""
    pa = u['passive'] or {}
    v = pa.get('variables') or {}
    txt = clean(pa.get('description'))
    low = txt.lower()
    attack = []
    if 'minDmg' in v and re.search(r'normal (melee |ranged )?attacks? deal an additional|all attacks deal an additional|after performing a normal attack', low):
        scope = ':melee' if 'normal melee attacks' in low else (':ranged' if 'normal ranged attacks' in low else '')
        attack.append('extra:1' + scope)
    defence = draft_defence(low)
    mentions = re.search(r'damage|armour|health|hit', low)
    review = 'Y' if (attack or defence or mentions) else 'N'
    return dict(Name=u['name'], Passive=pa.get('name', ''), Attack=';'.join(attack), Defence=';'.join(defence),
                Needs_Review=review, Notes='Draft: check both columns.' if review == 'Y' else '', Ability_Text=txt)


def sync_rows(path, cols, name_col, units, drafter, label):
    rows = {}
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            rows = {r['Name']: r for r in csv.DictReader(f)}
    added, changed = [], []
    for u in units:
        d = drafter(u)
        if u['name'] not in rows:
            rows[u['name']] = d
            added.append(u['name'])
            continue
        r = rows[u['name']]
        if r.get('Ability_Text') != d['Ability_Text']:
            r['Needs_Review'] = 'Y'
            r['Notes'] = ('Ability text changed; ' + r.get('Notes', '')).strip()
            changed.append(u['name'])
        r[name_col], r['Ability_Text'] = d[name_col], d['Ability_Text']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for name in sorted(rows):
            w.writerow({k: rows[name].get(k, '') for k in cols})
    if added:
        print(f'{label}: drafted {len(added)} new row(s): {", ".join(added)}')
    if changed:
        print(f'{label}: ability text changed, now flagged for review: {", ".join(changed)}')
    review = [n for n, r in rows.items() if r['Needs_Review'] == 'Y']
    if review:
        print(f'{label}: {len(review)} row(s) marked Needs_Review=Y: {", ".join(sorted(review))}')
    return rows


def sync_relics(g, units):
    """relic_abilities.csv: one row per relic, reviewed like the ability files"""
    rows = {}
    if os.path.exists(RELICS_CSV):
        with open(RELICS_CSV, newline='', encoding='utf-8') as f:
            rows = {r['Relic']: r for r in csv.DictReader(f)}
    by_relic = {}
    for u in units:
        if u['relic']:
            by_relic.setdefault(u['relic']['name'], []).append(u['name'])
    added, changed = [], []
    for v in g['items'].values():
        if not v.get('abilityId'):
            continue
        txt = clean((g['abilities'].get(v['abilityId']) or {}).get('description'))
        own = '; '.join(sorted(by_relic.get(v['name'], [])))
        if v['name'] not in rows:
            rows[v['name']] = dict(Relic=v['name'], Owners=own, Attack='', Defence='', Gear='', Needs_Review='Y',
                                   Notes='Draft: decide what counts.', Ability_Text=txt)
            added.append(v['name'])
            continue
        r = rows[v['name']]
        if r.get('Ability_Text') != txt:
            r['Needs_Review'] = 'Y'
            r['Notes'] = ('Relic text changed; ' + r.get('Notes', '')).strip()
            changed.append(v['name'])
        r['Owners'], r['Ability_Text'] = own, txt
    with open(RELICS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=RELIC_COLS)
        w.writeheader()
        for name in sorted(rows):
            w.writerow({k: rows[name].get(k, '') for k in RELIC_COLS})
    if added:
        print(f'relic_abilities.csv: drafted {len(added)} new row(s): {", ".join(added)}')
    if changed:
        print(f'relic_abilities.csv: relic text changed, now flagged for review: {", ".join(changed)}')
    review = [n for n, r in rows.items() if r['Needs_Review'] == 'Y']
    if review:
        print(f'relic_abilities.csv: {len(review)} row(s) marked Needs_Review=Y: {", ".join(sorted(review))}')
    unowned = [n for n in rows if not rows[n]['Owners']]
    if unowned:
        print('WARNING - relics with no character in the roster (check relic_owners.csv):', ', '.join(unowned))
    return rows


# ---------------------------------------------------------------- tokens
def parse_token(t):
    """'kind:arg[:scope][:vsTrait|Trait][@trig]' -> (kind, arg, scope, vs, trig_only)"""
    trig_only = t.endswith('@trig')
    t = t[:-5] if trig_only else t
    p = t.split(':')
    kind, arg = p[0], (p[1] if len(p) > 1 else '')
    if kind in ('suppress', 'stun'):
        return kind, '', arg or 'all', None, trig_only
    scope = p[2] if len(p) > 2 and p[2] else 'all'
    vs = set(p[3][2:].split('|')) if len(p) > 3 and p[3].startswith('vs') else None
    return kind, arg, scope, vs, trig_only


def tokens(cell):
    return [t.strip() for t in (cell or '').split(';') if t.strip()]


WHERE = {'all': '', 'melee': ' (melee)', 'ranged': ' (ranged)', 'psychic': ' (Psychic)', 'one': ' (first attack)',
         'after': ' (after the first attack)'}


def vs_text(vs):
    return f" vs {'/'.join(sorted(vs))}" if vs else ''


def attack_spec(u, row, level, trig, ab=None):
    """a passive's (or relic's) Attack tokens -> effects on the character's own normal attacks"""
    ab, text = (u['passive'] or {}) if ab is None else ab, (row or {}).get('Ability_Text', '')
    effects, desc = [], []
    for t in tokens((row or {}).get('Attack')):
        kind, arg, scope, vs, trig_only = parse_token(t)
        if trig_only and not trig:
            continue
        e = dict(kind=kind, scope=scope, vs=vs)
        if kind in ('extra', 'extrahalf'):
            # 'extra:1|2' = part 1 normally, part 2 against a Big Target (Kariyan's Legacy of Combat).
            # 'A' in front of a part means the numbers come from the character's ACTIVE ability, for the
            # passives an active hands out for the rest of the battle (Abaddon's Drach'nyen).
            def part_of(tok):
                if tok[:1] == 'A':
                    act = u.get('ability') or {}
                    return build_part(act, act.get('description', ''), tok[1:], level)
                return build_part(ab, text, tok, level)
            first_part, _, big = arg.partition('|')
            e['part'] = part_of(first_part)
            if big:
                e['part_big'] = part_of(big)
            when = ' once the target is at or below half health' if kind == 'extrahalf' else ''
            desc.append(f"+{part_text(e['part'])} on each attack{WHERE[scope]}{vs_text(vs)}{when}"
                        + (f" (+{part_text(e['part_big'])} against a Big Target)" if big else ''))
        elif kind == 'follow':
            desc.append('melee attacks are followed by a normal ranged attack')
        elif kind in ('flat', 'pct', 'pierce', 'hits', 'armignore', 'ramp', 'armpct'):
            e['value'] = value_of(ab, arg, level)
            fmt = {'flat': '+{:,.0f} Damage', 'pct': '+{:.0f}% damage', 'pierce': '+{:.0f}% pierce',
                   'hits': '+{:.0f} hit(s)', 'armignore': 'ignores {:,.0f} Armour', 'armpct': "target's Armour -{:.0f}%",
                   'ramp': 'each hit +{:,.0f} more than the last'}[kind]
            desc.append(fmt.format(e['value']) + WHERE[scope] + vs_text(vs))
        else:
            sys.exit(f"{u['name']}: unknown Attack token {t!r} in passive_abilities.csv")
        effects.append(e)
    return (effects, desc) if effects else None


def defence_spec(u, ab, cell, level, trig):
    """Defence tokens (active or passive) -> effects on damage the character takes"""
    ds = new_ds()
    for t in tokens(cell):
        kind, arg, scope, vs, trig_only = parse_token(t)
        if trig_only and not trig:
            continue
        w = WHERE.get(scope, '') + vs_text(vs)
        if kind in ('suppress', 'stun'):
            ds['enemy'].append((SUPPRESSED if kind == 'suppress' else STUNNED, scope, None))
            who = {'one': 'one enemy', 'melee': 'adjacent enemies'}.get(scope, 'nearby enemies')
            ds['text'].append(('suppresses ' if kind == 'suppress' else 'stuns ') + who)
        elif kind == 'pct':
            v = min(value_of(ab, arg, level), 95)
            ds['pct'].append((1 - v / 100, scope, vs)); ds['text'].append(f'takes -{v:.0f}% damage{w}')
        elif kind == 'epct':
            v = min(value_of(ab, arg, level), 95)
            ds['enemy'].append((1 - v / 100, scope, vs)); ds['text'].append(f'enemies deal -{v:.0f}% damage{w}')
        elif kind == 'flat':
            v = value_of(ab, arg, level)
            ds['flat'].append((v, scope, vs)); ds['text'].append(f'takes -{v:,.0f} damage per hit{w}')
        elif kind == 'hitsless':
            v = value_of(ab, arg, level)
            ds['hitsless'].append((v, scope, vs)); ds['text'].append(f'attackers score -{v:.0f} hit{w}')
        elif kind == 'pctcap':
            pv, cv = arg.split('/')
            p, c = value_of(ab, pv, level), value_of(ab, cv, level)
            ds['pctcap'].append((p / 100, c, scope, vs)); ds['text'].append(f'takes -{p:.0f}% damage, max -{c:,.0f} a hit{w}')
        elif kind == 'armour':
            v = value_of(ab, arg, level)
            ds['armour'] += v; ds['text'].append(f'+{v:,.0f} Armour')
        elif kind == 'armourpass':
            v = value_of(ab, arg, level)
            ds['pass2'] += v; ds['text'].append(f'attacks go through {v:,.0f} Armour an extra time')
        elif kind == 'guard':
            hv, av = arg.split('/')
            h, a_ = value_of(ab, hv, level), value_of(ab, av, level)
            ds['guard'] = (h, a_); ds['text'].append(f'a bodyguard ({h:,.0f} health, {a_:,.0f} Armour) takes the hits first')
        elif kind == 'cap_first':
            v = value_of(ab, arg, level)
            ds['cap_first'] = v / 100; ds['text'].append(f'the first attack each turn takes at most {v:.0f}% of its health')
        elif kind == 'heal':
            v = value_of(ab, arg, level)
            ds['heal'] += v; ds['text'].append(f'+{v:,.0f} health')
        elif kind == 'lose':
            v = value_of(ab, arg, level)
            ds['hpmult'] *= 1 - v / 100; ds['text'].append(f'loses {v:.0f}% of its health')
        elif kind == 'setpct':
            v = value_of(ab, arg, level)
            ds['hpmult'] *= v / 100; ds['text'].append(f'drops to {v:.0f}% health')
        else:
            sys.exit(f"{u['name']}: unknown Defence token {t!r}")
    return ds if ds['text'] else None


def new_ds():
    return dict(pct=[], flat=[], enemy=[], hitsless=[], pctcap=[], heal=0.0, hpmult=1.0, armour=0.0,
                cap_first=None, pass2=0.0, guard=None, bc=0.0, bd=0.0, ccr=0.0, cdr=0.0, text=[])


def merge_defence(*specs):
    specs = [s for s in specs if s]
    if not specs:
        return None
    out = new_ds()
    for s in specs:
        for k in ('pct', 'flat', 'enemy', 'hitsless', 'pctcap', 'text'):
            out[k] += s[k]
        out['heal'] += s['heal']; out['hpmult'] *= s['hpmult']; out['armour'] += s['armour']
        out['pass2'] += s['pass2']; out['guard'] = out['guard'] or s['guard']
        for k in ('bc', 'bd', 'ccr', 'cdr'):
            out[k] += s[k]
        if s['cap_first'] is not None:
            out['cap_first'] = s['cap_first'] if out['cap_first'] is None else min(out['cap_first'], s['cap_first'])
    return out


def gear_spec(u, ab, cell, level, trig, text=''):
    """Gear tokens (only used with standard gear on): crit and block effects of an ability.
    Returns (attacker effects, defence ds or None, text)."""
    off, ds, desc_extra = [], new_ds(), []
    text_in, text = text, []
    for t in tokens(cell):
        kind, arg, scope, vs, trig_only = parse_token(t)
        if trig_only and not trig:
            continue
        v = value_of(ab, arg, level) if arg else 0.0
        w = WHERE.get(scope, '') + vs_text(vs)
        if kind in ('critchance', 'critdmgpct', 'dmgfromblock'):
            off.append(dict(kind=kind, value=v / 100, scope=scope, vs=vs))
            text.append({'critchance': f'+{v:.0f}% crit chance', 'critdmgpct': f'+{v:.0f}% Crit Damage',
                         'dmgfromblock': f'+{v:.0f}% of its Block Damage as Damage'}[kind] + w)
        elif kind == 'critdmg':
            off.append(dict(kind=kind, value=v, scope=scope, vs=vs)); text.append(f'+{v:,.0f} Crit Damage{w}')
        elif kind == 'critextra':
            part = build_part(ab, text_in, arg, level)
            off.append(dict(kind=kind, value=0, part=part, scope=scope, vs=vs))
            text.append(f'+{part_text(part)} when the attack crits{w}')
        elif kind == 'alwayscrit':
            off.append(dict(kind=kind, value=1, scope=scope, vs=vs)); text.append('always crits')
        elif kind == 'blockchance':
            ds['bc'] += v / 100; ds['text'].append(f'+{v:.0f}% block chance'); text.append(f'+{v:.0f}% block chance')
        elif kind == 'blockdmg':
            ds['bd'] += v; ds['text'].append(f'+{v:,.0f} Block Damage'); text.append(f'+{v:,.0f} Block Damage')
        elif kind == 'critreduce':
            c, dd = arg.split('/')
            cv, dv = value_of(ab, c, level), value_of(ab, dd, level)
            ds['ccr'] += cv / 100; ds['cdr'] += dv
            ds['text'].append(f'attackers -{cv:.0f}% crit chance, -{dv:,.0f} Crit Damage')
            text.append(ds['text'][-1])
        else:
            sys.exit(f"{u['name']}: unknown Gear token {t!r}")
    has_ds = ds['bc'] or ds['bd'] or ds['ccr'] or ds['cdr']
    return off, (ds if has_ds else None), text + desc_extra


def active_spec(u, row, level):
    """an active_abilities.csv row -> the character's opening turn (offence)"""
    ab = u['ability'] or {}
    if not row or row['Kind'] != 'damage':
        return None
    text = row['Ability_Text']
    parts = [build_part(ab, text, t, level) for t in tokens(row['Damage_Parts'])]
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
        consts = ab.get('constants') or {}
        spec['bonus'] = dict(dmg=ability_value(ab, bonus, level), hits=int(ability_value(ab, 'nrOfHits', level) or 1),
                             type=dtype(consts.get('damageProfile') or 'Physical'))
    return spec


def describe_active(spec):
    if not spec:
        return ''
    bits = [part_text(p) for p in spec['parts']]
    extra = ''
    if spec.get('bonus'):
        extra = f" with +{part_text(spec['bonus'])}"
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


def one_round(cell):
    """True if an active's Defence protects for a whole enemy turn (not just one attack or extra health),
    so the ATTACKS_PER_TURN limit changes its result"""
    for t in tokens(cell):
        kind, _, scope, _, _ = parse_token(t)
        if kind in ('pct', 'flat', 'epct', 'suppress', 'stun', 'hitsless', 'pctcap') and scope != 'one':
            return True
    return False


def describe_defence(ds):
    return '; '.join(ds['text']) if ds else ''


# ---------------------------------------------------------------- damage model
def hit_value(D, A, p, gravis, pass2=0.0):
    """one hit after armour. gravis = Mk X Gravis (armour a second time);
    pass2 = an extra armour pass of that value (Uthar's Fortify Takeover)"""
    y = max(D - A, D * p)
    if gravis and p < 1:
        y = max(y - A, y * p)
    if pass2 and p < 1:
        y = max(y - pass2, y * p)
    return y


def _applies(e, kind, first, d):
    sc = e['scope']
    ok = sc == 'all' or sc == kind or (sc == 'after' and not first) or (sc == 'one' and first)
    tags = d['traits'] | {d.get('alliance')}
    # vsnot: support buffs that apply to every enemy except these (support_model.py)
    return ok and (e['vs'] is None or bool(e['vs'] & tags)) and not (e.get('vsnot') and e['vsnot'] & tags)


def _chain(c, n):
    """expected number of hits in a crit/block chain: it starts on hit 1 and each later hit
    re-rolls until one fails (wiki HDTW_Damage)"""
    return sum(c ** k for k in range(1, max(1, int(n)) + 1))


def crit_of(a, kind, first, d, trig, gearx=None, dblk=None):
    """(crit chance, Crit Damage) of the attacker's hits, or None without gear.
    kind = 'melee' / 'ranged' / 'ability' (ability hits only get effects with scope 'all')."""
    g = a.get('g')
    if not g:
        return None
    eff = [e for e in (a.get('pg') or []) + (gearx or []) if _applies(e, kind, first, d)]
    cc = g['cc'] + sum(e['value'] for e in eff if e['kind'] == 'critchance')
    cd = g['cd'] + sum(e['value'] for e in eff if e['kind'] == 'critdmg')
    if trig and 'ActOfFaith' in a['traits']:
        cc += 0.10; cd *= 1.25                            # one stack
    if trig and 'ThrillSeekers' in a['traits']:
        cc += 0.15                                        # Thrilled
    cd *= _prod(1 + e['value'] for e in eff if e['kind'] == 'critdmgpct')
    if dblk:
        cc -= dblk['ccr']; cd -= dblk['cdr']
    if any(e['kind'] == 'alwayscrit' for e in eff):
        cc = 1.0
    return min(max(cc, 0.0), 1.0), max(cd, 0.0)


def block_of(d, ds):
    """the defender's block (chance, Block Damage) and crit reductions: gear + abilities"""
    g = d.get('g')
    if not g and not ds:
        return None
    x = dict(bc=(g['bc'] if g else 0.0) + (ds['bc'] if ds else 0.0), bd=(g['bd'] if g else 0.0) + (ds['bd'] if ds else 0.0),
             ccr=ds['ccr'] if ds else 0.0, cdr=ds['cdr'] if ds else 0.0)
    x['bc'] = min(x['bc'], 1.0)
    return x


def normal_attack(a, d, w, trig, dmg_override=None, first=False, hits_minus=0, follow=True, gearx=None, dblk=None,
                  half=False):
    """one normal attack by a on d with weapon w: (damage, ignores Terminator Armour).
    Includes a's passive (a['ps']) and, with gear, crits (a['g'], a['pg'], gearx) and d's blocks (dblk).
    See DAMAGE_MODEL.md."""
    at, dt = a['traits'], d['traits']
    melee = w['kind'] == 'melee'
    eff = [e for e in (a.get('ps') or ([], []))[0] if _applies(e, w['kind'], first, d)]
    add = lambda k: sum(e['value'] for e in eff if e['kind'] == k)
    n, p = w['hits'] + int(add('hits')), min(1.0, w['pierce'] + add('pierce') / 100)
    D = (dmg_override if dmg_override is not None else a['dmg']) + add('flat')
    effg = [e for e in (a.get('pg') or []) + (gearx or []) if _applies(e, w['kind'], first, d)] if a.get('g') else []
    D += sum(e['value'] * a['g']['bd'] for e in effg if e['kind'] == 'dmgfromblock')
    A = max(0.0, d['arm'] - add('armignore')) * (1 - min(add('armpct'), 100) / 100)
    psychic = w['type'] in ('Psychic', 'Direct')
    if melee and 'Parry' in dt and n > 1:
        n -= 1
    if not melee and 'Camouflage' in dt:
        n = max(1, n - (2 if (trig and w['range'] >= 3) else 1))
    if hits_minus:
        n = max(1, n - hits_minus)
    D += add('ramp') * (n - 1) / 2                        # Lhykhis: each hit +X more than the last
    if trig:
        if 'GetStuckIn' in at: n += (n // 2) * 0.3
        if 'LetTheGalaxyBurn' in at: n += 0.33
        if 'WeaverOfFate' in at: D *= 1.2
        if 'ContagionsOfNurgle' in at and melee: A *= 0.8
    y = hit_value(D, A, p, 'MkXGravis' in dt, d.get('pass2', 0))
    m = _prod(1 + e['value'] / 100 for e in eff if e['kind'] == 'pct')
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
    cr = crit_of(a, w['kind'], first, d, trig, gearx, dblk)
    if cr and cr[0] > 0:
        # a crit adds Crit Damage before armour and skips Mk X Gravis
        per_crit = hit_value(D + cr[1], A, p, False, d.get('pass2', 0)) * m
        total += _chain(cr[0], n) * max(per_crit - per_hit, 0)
        for e in effg:                                    # relic: extra hits when the attack crits (Maugetar)
            if e['kind'] == 'critextra':
                total += cr[0] * ability_hits(e['part'], d, 0.0, None, dblk)[0]
    if dblk and dblk['bc'] > 0 and not psychic:
        total -= _chain(dblk['bc'], n) * min(dblk['bd'], per_hit)   # blocks come last; Psychic can't be blocked
    if trig and not psychic:
        # random blocks from traits: the chain starts on hit 1, each later hit re-rolls until one fails
        for chance, block in (((0.25, 0.5 * d['dmg']) if 'Daemon' in dt else (0, 0)),
                              ((0.10, d['arm']) if 'BeastSlayer' in dt else (0, 0))):
            if chance:
                total -= _chain(chance, n) * min(block, per_hit)
    for e in eff:                                         # passive: extra hits after each attack
        if e['kind'] == 'extra' or (half and e['kind'] == 'extrahalf'):
            part = e['part_big'] if (e.get('part_big') and 'BigTarget' in d['traits']) else e['part']
            # these are attacks the character performs, so the traits that lift an attack lift them too
            # (Rapid Assault, Beast Slayer against a Big Target, Crushing Strike...) - m, worked out above
            total += ability_hits(part, d, 0.0, cr, dblk)[0] * m
    if follow and melee and any(e['kind'] == 'follow' for e in eff):
        rw = next((x for x in a['weapons'] if x['kind'] == 'ranged'), None)
        if rw:
            total += normal_attack(a, d, rw, trig, dmg_override, first, hits_minus, False, gearx, dblk)[0]
    return max(total, 1.0), psychic


def ability_hits(part, d, flat_red=0.0, crit=None, block=None):
    """ability damage: armour, pierce and Mk X Gravis (abilities aren't 'normal attacks'),
    plus crits (unless the ability 'cannot Crit') and the defender's blocks when there is gear"""
    p = PIERCE.get(part['type'], .2)
    D = max(part['dmg'] - flat_red, 0)
    psychic = part['type'] in ('Psychic', 'Direct')
    y = hit_value(D, d['arm'], p, 'MkXGravis' in d['traits'], d.get('pass2', 0))
    total = y * part['hits']
    if crit and crit[0] > 0 and part.get('crit', True):
        yc = hit_value(D + crit[1], d['arm'], p, False, d.get('pass2', 0))
        total += _chain(crit[0], part['hits']) * max(yc - y, 0)
    if block and block['bc'] > 0 and not psychic:
        total -= _chain(block['bc'], part['hits']) * min(block['bd'], y)
    return max(total, 0.0), psychic


def _def_ok(scope, vs, kind, first_turn, psychic, a):
    ok = (scope == 'all' or scope == kind or (scope == 'one' and first_turn) or (scope == 'after' and not first_turn)
          or (scope == 'psychic' and psychic))
    return ok and (vs is None or bool(vs & (a['traits'] | {a.get('alliance')})))


def one_attack(a, d, w, trig, ds, first_seq, first_turn=None, dmg_override=None, gearx=None, half=False):
    """a normal attack after the defender's defensive effects (ds may be None).
    first_seq = the first attack of the whole kill (the attacker's own 'after' effects);
    first_turn = the first attack of an enemy turn (the defender's 'one' effects)."""
    first_turn = first_seq if first_turn is None else first_turn
    dblk = block_of(d, ds)
    if not ds:
        return normal_attack(a, d, w, trig, dmg_override, first_seq, gearx=gearx, dblk=dblk, half=half)
    psychic = w['type'] in ('Psychic', 'Direct')
    ok = lambda sc, vs: _def_ok(sc, vs, w['kind'], first_turn, psychic, a)
    flat = sum(v for v, sc, vs in ds['flat'] if ok(sc, vs))
    hits_minus = int(sum(v for v, sc, vs in ds['hitsless'] if ok(sc, vs)))
    base = dmg_override if dmg_override is not None else a['dmg']
    dmg, psy = normal_attack(a, d, w, trig, max(base - flat, 0), first_seq, hits_minus, gearx=gearx, dblk=dblk,
                             half=half)
    dmg *= _prod(m for m, sc, vs in ds['pct'] if ok(sc, vs)) * _prod(m for m, sc, vs in ds['enemy'] if ok(sc, vs))
    for p, cap, sc, vs in ds['pctcap']:
        if ok(sc, vs):
            dmg -= min(p * dmg, cap * w['hits'])
    return max(dmg, 1.0), psy


def part_vs_defence(part, d, ds, first_turn, a=None, trig=False, gearx=None):
    """an ability damage part after the defender's defensive effects (and gear, when on)"""
    psychic = part['type'] in ('Psychic', 'Direct')
    dblk = block_of(d, ds)
    cr = crit_of(a, 'ability', first_turn, d, trig, gearx, dblk) if a else None
    if not ds:
        return ability_hits(part, d, 0.0, cr, dblk)
    ok = lambda sc, vs: vs is None and (sc == 'all' or (sc == 'one' and first_turn)
                                        or (sc == 'after' and not first_turn) or (sc == 'psychic' and psychic))
    flat = sum(v for v, sc, vs in ds['flat'] if ok(sc, vs))
    dmg, psy = ability_hits(part, d, flat, cr, dblk)
    dmg *= _prod(m for m, sc, vs in ds['pct'] if ok(sc, vs))
    dmg *= _prod(m for m, sc, vs in ds['enemy'] if ok(sc, vs))
    return dmg, psy


def best_attack(a, d, trig, ds, first_seq, first_turn, kind=None, dmg_override=None, gearx=None, half=False):
    """(damage, ignores TA, weapon) of the attacker's best normal attack in this situation"""
    ws = [w for w in a['weapons'] if not kind or w['kind'] == kind] or a['weapons']
    best = None
    for w in ws:
        dmg, psy = one_attack(a, d, w, trig, ds, first_seq, first_turn, dmg_override, gearx, half)
        if best is None or dmg > best[0]:
            best = (dmg, psy, w)
    return best


def opener(a, d, trig, spec, ds):
    """the attacks of the turn the character uses its active ability, in order"""
    gx = spec.get('gear')
    attacks = [part_vs_defence(p, d, ds, i == 0, a, trig, gx) for i, p in enumerate(spec['parts'])]
    bonus_used = False

    def normal_with_bonus(kind, override):
        nonlocal bonus_used
        if spec.get('flat') and not bonus_used:
            override = (override if override is not None else a['dmg']) + spec['flat']
        first = not attacks
        dmg, psy, _ = best_attack(a, d, trig, ds, first, first, kind, override, gx)
        if spec.get('bonus') and not bonus_used:
            dmg += part_vs_defence(spec['bonus'], d, ds, False, a, trig, gx)[0]
        bonus_used = True
        return dmg, psy
    if spec['normal'] in ('Y', 'PCT'):
        override = min(a['dmg'] * spec['pct'], spec['cap'] or 1e9) if spec['normal'] == 'PCT' else None
        attacks.append(normal_with_bonus(spec['weapon'], override))
    if spec['same_turn']:
        attacks.append(normal_with_bonus(spec['weapon'], None))
    return attacks


def kill_count(first, early, turn_first, later, d, hp, cap_first=None, regen=None, half=0.0):
    """attacks to kill, one attack at a time. An enemy turn is ATTACKS_PER_TURN attacks.
    first = list of (damage, ignores_TA) making up attack 1 (several parts for an active);
    early = damage of attacks 2..ATTACKS_PER_TURN (inside the first enemy turn);
    turn_first = (damage, ignores_TA) of the first attack of each later turn; later = the rest.
    Terminator Armour and cap_first (Judh) apply to the first attack of every turn.
    regen (support_model.py only; the roster map never passes it): dict(turn=health back before each later
    enemy turn, hit=health back after each attack, shield=a shield at the start of every enemy turn,
    shield_first=a shield for the first enemy turn only). Healing never goes above hp."""
    if regen:
        return _kill_count_regen(first, early, turn_first, later, d, hp, cap_first, regen, half)
    ta = 'TerminatorArmour' in d['traits']
    left = hp
    for i in range(5000):
        if i == 0:
            dmg = sum(x * (0.25 if (j == 0 and ta and not p) else 1) for j, (x, p) in enumerate(first))
        elif i % ATTACKS_PER_TURN == 0:
            dmg = turn_first[0] * (0.25 if (ta and not turn_first[1]) else 1)
        elif i < ATTACKS_PER_TURN:
            dmg = early
        else:
            dmg = later
        if cap_first is not None and i % ATTACKS_PER_TURN == 0:
            dmg = min(dmg, cap_first * left)
        if half and left <= hp / 2:           # Havyr: the extra attack only lands on a wounded target
            dmg += half
        dmg = max(dmg, 1.0)
        if dmg >= left:
            return i + left / dmg
        left -= dmg
    return 5000.0


def _kill_count_regen(first, early, turn_first, later, d, hp, cap_first, regen, half=0.0):
    """kill_count with healing between and during enemy turns, and shields (support_model.py)"""
    ta = 'TerminatorArmour' in d['traits']
    left, shield = hp, 0.0
    limit = int(regen.get('limit', 5000))        # support_model stops at its 10-turn horizon
    for i in range(limit):
        if i % ATTACKS_PER_TURN == 0:
            if i:
                left = min(hp, left + regen.get('turn', 0.0))
            shield = regen.get('shield', 0.0) + (regen.get('shield_first', 0.0) if i == 0 else 0.0)
        if i == 0:
            dmg = sum(x * (0.25 if (j == 0 and ta and not p) else 1) for j, (x, p) in enumerate(first))
        elif i % ATTACKS_PER_TURN == 0:
            dmg = turn_first[0] * (0.25 if (ta and not turn_first[1]) else 1)
        elif i < ATTACKS_PER_TURN:
            dmg = early
        else:
            dmg = later
        if cap_first is not None and i % ATTACKS_PER_TURN == 0:
            dmg = min(dmg, cap_first * left)
        if half and left <= hp / 2:
            dmg += half
        dmg = max(dmg, 1.0)
        soak = min(shield, dmg)
        shield -= soak
        if dmg - soak >= left:
            return i + (left + soak) / dmg
        left = min(hp, left - (dmg - soak) + regen.get('hit', 0.0))
    return float(limit)


def _with_defence(d, ds):
    if ds and (ds['armour'] or ds['pass2']):
        return dict(d, arm=d['arm'] + ds['armour'], pass2=ds['pass2'])
    return d


def attacks_to_kill(a, d, trig, spec=None, ds_round=None, ds_rest=None, regen=None):
    """(attacks, best attack kind, normal attack damage, used the active).
    spec = the attacker's active (offence); a['ps'] = the attacker's passive.
    ds_round = the defender's defence during the first enemy turn (active + passive);
    ds_rest = the defender's defence after that (passive only): active effects last one round."""
    d1, d2 = _with_defence(d, ds_round), _with_defence(d, ds_rest)
    hp = d['hp'] * (ds_round['hpmult'] if ds_round else 1) + (ds_round['heal'] if ds_round else 0)
    cap = next((x['cap_first'] for x in (ds_rest, ds_round) if x and x['cap_first'] is not None), None)
    a1 = best_attack(a, d1, trig, ds_round, True, True)
    early = best_attack(a, d1, trig, ds_round, False, False)[0]
    tf = best_attack(a, d2, trig, ds_rest, False, True)
    later_dmg, _, later_w = best_attack(a, d2, trig, ds_rest, False, False)
    half = 0.0
    if any(e['kind'] == 'extrahalf' for e in (a.get('ps') or ([], []))[0]):
        half = max(best_attack(a, d2, trig, ds_rest, False, False, half=True)[0] - later_dmg, 0.0)
    k = kill_count([a1[:2]], early, tf[:2], later_dmg, d, hp, cap, regen, half)
    used = False
    if spec:
        k_act = kill_count(opener(a, d1, trig, spec, ds_round), early, tf[:2], later_dmg, d, hp, cap, regen, half)
        if k_act < k:
            k, used = k_act, True
    guard = (ds_round or {}).get('guard') or (ds_rest or {}).get('guard')
    if guard:
        # a bodyguard (Kell) takes the attacks first, with its own health and Armour and no traits
        gh, ga = guard
        body = dict(name='guard', hp=gh, arm=ga, dmg=0, traits=set(), weapons=[])
        k += gh / max(one_attack(a, body, later_w, trig, None, False)[0], 1.0)
    return k, later_w['kind'], later_dmg, used


def scenario_keys():
    """(key, traits triggered, ability level or None, active on, gear on)"""
    keys = [('base', False, None, False, False)]
    for gear in (False, True):
        for trig in (False, True):
            for lv in ABILITY_LEVELS:
                for act in (False, True):
                    keys.append((f"{'trig' if trig else 'base'}_l{lv}{'_a' if act else ''}{'_g' if gear else ''}",
                                 trig, lv, act, gear))
    return keys


def run_scenarios(units, specs, keep=None):
    """specs[(level, trig, gear)] = dict(active=, active_def=, active_gdef=, passive=, passive_def=,
    passive_goff=, passive_gdef=) keyed by name. keep: a dict that receives every scenario's full
    matchup table (attacks x 100, attacker-major, in units order) for the typical-character page."""
    out = {}
    for key, trig, lv, act, gear in scenario_keys():
        sp = specs.get((lv, trig, gear)) if lv else None
        U = [dict(u, hp=u['hp'] + u['gear']['hp'], arm=u['arm'] + u['gear']['arm'], g=u['gear']) if gear
             else dict(u, g=None) for u in units]
        for u in U:
            n = u['name']
            u['ps'] = sp['passive'].get(n) if sp else None
            u['pg'] = sp['passive_goff'].get(n) if sp else None
        rnd = {u['name']: merge_defence(*((sp['active_def'].get(u['name']), sp['active_gdef'].get(u['name'])) if act else ()),
                                        sp['passive_def'].get(u['name']), sp['passive_gdef'].get(u['name']))
               if sp else None for u in U}
        rest = {u['name']: merge_defence(sp['passive_def'].get(u['name']), sp['passive_gdef'].get(u['name']))
                if sp else None for u in U}
        K = {a['name']: {d['name']: attacks_to_kill(a, d, trig, sp['active'].get(a['name']) if (sp and act) else None,
                                                    rnd[d['name']], rest[d['name']]) for d in U}
             for a in U}
        if keep is not None and lv:
            keep[key] = [round(K[a['name']][d['name']][0] * 100) for a in U for d in U]
        dmg = {a: st.median(v[0] for v in K[a].values()) for a in K}
        tough = {d['name']: st.median(K[a['name']][d['name']][0] for a in U) for d in U}
        kinds = {a: max(('melee', 'ranged'), key=lambda k: sum(1 for v in K[a].values() if v[1] == k)) for a in K}
        rd = {n: i + 1 for i, n in enumerate(sorted(dmg, key=dmg.get))}
        rt = {n: i + 1 for i, n in enumerate(sorted(tough, key=tough.get, reverse=True))}
        out[key] = {n: dict(d=round(dmg[n], 3), t=round(tough[n], 3), rd=rd[n], rt=rt[n], k=kinds[n]) for n in dmg}
        if key == STANDARD:
            out['creed'] = {n: dict(to=round(K[n]['Castellan Creed'][2]), frm=round(K['Castellan Creed'][n][2]),
                                    kill=round(K[n]['Castellan Creed'][0], 2), die=round(K['Castellan Creed'][n][0], 2))
                            for n in dmg}
    return out


# ---------------------------------------------------------------- outputs
def pretty(t):
    s = re.sub(r'(?<!^)(?=[A-Z])', ' ', t).replace(' Of ', ' of ').replace(' The ', ' the ')
    return {'Martial Katah': "Martial Ka'tah", 'Weaver of Fate': 'Weaver of Fates'}.get(s, s)


def describe_gear_kit(sp, name):
    return '; '.join(sp['active_gtext'].get(name, []) + sp['passive_gtext'].get(name, []))


def describe_passive(sp, name):
    bits = []
    ps = sp['passive_only'].get(name)
    if ps:
        bits += ps[1]
    ds = sp['passive_only_def'].get(name)
    if ds:
        bits += ds['text']
    return '; '.join(bits)


def generic(key):
    """scenario key with the tier's ability levels replaced by lv1/lv2 (for the long-format CSV)"""
    for i, lv in enumerate(ABILITY_LEVELS):
        key = key.replace(f'_l{lv}', f'_lv{i + 1}')
    return key


def tier_rows(units, res, actives, passives, specs):
    """rows of tacticus_stats.csv for the current tier"""
    keys = [k for k, *_ in scenario_keys()]
    out = []
    for u in sorted(units, key=lambda u: u['name']):
        wp = {x['kind']: x for x in u['weapons']}
        m, r = wp.get('melee'), wp.get('ranged')
        n = u['name']
        row = dict(Tier=TIER['label'], Name=n, Faction=u['faction'], Alliance=u['alliance'],
                   Health=round(u['hp']), Damage=round(u['dmg']), Armour=round(u['arm']),
                   Standard_Gear='; '.join(u['gear']['items']), Relic=u['relic']['name'] if (RELICS and u['relic']) else '',
                   Melee_Type=m['type'] if m else '', Melee_Hits=m['hits'] if m else '', Melee_Pierce=f"{m['pierce']:.0%}" if m else '',
                   Ranged_Type=r['type'] if r else '', Ranged_Hits=r['hits'] if r else '',
                   Ranged_Pierce=f"{r['pierce']:.0%}" if r else '', Ranged_Range=r['range'] if r else '',
                   Passive_Ability=passives[n]['Passive'], Active_Ability=actives[n]['Active'], Active_Kind=actives[n]['Kind'],
                   Ability_Level_1=ABILITY_LEVELS[0], Ability_Level_2=ABILITY_LEVELS[1])
        for i, lv in enumerate(ABILITY_LEVELS):
            row[f'Passive_Counted_Lv{i + 1}'] = describe_passive(specs[(lv, False, False)], n)
            row[f'Active_Counted_Lv{i + 1}'] = describe_active(specs[(lv, False, False)]['active'].get(n))
            row[f'Active_Defence_Lv{i + 1}'] = describe_defence(specs[(lv, False, False)]['active_def'].get(n))
            row[f'Gear_Kit_Lv{i + 1}'] = describe_gear_kit(specs[(lv, False, True)], n)
        row['Relic_Effect'] = '; '.join(specs[(ABILITY_LEVELS[0], False, True)]['relic_text'].get(n, []))
        for k in keys:
            row[f'Damage_{generic(k)}'] = f"{res[k][n]['d']:.2f}"
        for k in keys:
            row[f'Toughness_{generic(k)}'] = f"{res[k][n]['t']:.2f}"
        out.append(row)
    return out


def tier_html(units, res, specs):
    """per-character data for the current tier"""
    out = {}
    L = ABILITY_LEVELS
    for u in units:
        n = u['name']
        out[n] = dict(hp=round(u['hp']), dmg=round(u['dmg']), arm=round(u['arm']),
                      gear=dict(items=u['gear']['items'],
                                kit={lv: describe_gear_kit(specs[(lv, False, True)], n) for lv in L},
                                kit_trig={lv: describe_gear_kit(specs[(lv, True, True)], n) for lv in L}),
                      relic='; '.join(specs[(L[0], False, True)]['relic_text'].get(n, [])),
                      active=dict(counted={lv: describe_active(specs[(lv, False, False)]['active'].get(n)) for lv in L},
                                  defence={lv: describe_defence(specs[(lv, False, False)]['active_def'].get(n)) for lv in L}),
                      passive=dict(counted={lv: describe_passive(specs[(lv, False, False)], n) for lv in L},
                                   triggered={lv: describe_passive(specs[(lv, True, False)], n) for lv in L}),
                      s={k: res[k][n] for k, *_ in scenario_keys()},
                      creed=res['creed'][n])
    return out


def write_stats(rows, version):
    cols = list(rows[0].keys()) + ['Game_Version']
    with open(STATS_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, Game_Version=version))


def write_html(units, per_tier, actives, passives, relics, version):
    chars = []
    for u in units:
        n = u['name']
        row, prow = actives.get(n, {}), passives.get(n, {})
        rrow = relics.get(u['relic']['name'], {}) if u['relic'] else {}
        chars.append(dict(name=n, faction=u['faction'], alliance=u['alliance'],
                          weapons=[f"{w['kind'].title()}: {w['type']} ×{w['hits']}" for w in u['weapons']],
                          counted=sorted(pretty(t) for t in u['traits'] & COUNTED),
                          situational=sorted(pretty(t) for t in u['traits'] & SITUATIONAL),
                          active=dict(name=row.get('Active', ''), kind=row.get('Kind', ''), notes=row.get('Notes', ''),
                                      round=one_round(row.get('Defence')), review=row.get('Needs_Review') == 'Y'),
                          passive=dict(name=prow.get('Passive', ''), notes=prow.get('Notes', ''),
                                       review=prow.get('Needs_Review') == 'Y'),
                          relic=dict(name=u['relic']['name'] if u['relic'] else '', notes=rrow.get('Notes', ''),
                                     review=rrow.get('Needs_Review') == 'Y'),
                          t={tk: per_tier[tk][n] for tk in per_tier}))
    data = dict(version=version, tiers=[dict(key=t['key'], label=t['label'], about=t['about'], levels=list(t['levels']))
                                        for t in TIERS], chars=chars)
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('map_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False)))


def write_typical(units, tables, version):
    """typical-character.html: every matchup table, so the page can show any character's 117 answers
    under any of the map's settings. tables[tier key][scenario key] = flat list from run_scenarios(keep=)."""
    data = dict(version=version, tiers=[dict(key=t['key'], label=t['label'], levels=list(t['levels'])) for t in TIERS],
                chars=[dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in units], k=tables, start='Kharn')
    with open(TYPICAL_TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('typical_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT_TYPICAL, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))


def creed_check(path, units):
    """compare the plain stat line against the owner's Creed test numbers. Those numbers include
    Rapid Assault and Ranged Specialist (the game shows them), so this check adds them back.
    They also include passives at the owner's skill levels, which this check leaves out."""
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


def build_specs(units, actives, passives, relics):
    """every ability effect for the current tier: specs[(level, trig, gear)]"""
    specs = {}
    for lv in ABILITY_LEVELS:
        for trig in (False, True):
            for gear in (False, True):
                sp = dict(active={}, active_def={}, active_gdef={}, active_gtext={},
                          passive={}, passive_def={}, passive_goff={}, passive_gdef={}, passive_gtext={},
                          passive_only={}, passive_only_def={}, relic_text={})
                for u in units:
                    n, arow, prow = u['name'], actives.get(u['name']), passives.get(u['name'])
                    try:
                        if (x := active_spec(u, arow, lv)):
                            sp['active'][n] = x
                        if (x := defence_spec(u, u['ability'] or {}, (arow or {}).get('Defence'), lv, trig)): sp['active_def'][n] = x
                        if (x := attack_spec(u, prow, lv, trig)): sp['passive'][n] = sp['passive_only'][n] = x
                        if (x := defence_spec(u, u['passive'] or {}, (prow or {}).get('Defence'), lv, trig)):
                            sp['passive_def'][n] = sp['passive_only_def'][n] = x
                        if gear:
                            off, gds, txt = gear_spec(u, u['ability'] or {}, (arow or {}).get('Gear'), lv, trig,
                                                      (arow or {}).get('Ability_Text', ''))
                            if off and n in sp['active']:
                                sp['active'][n] = dict(sp['active'][n], gear=off)
                            if gds: sp['active_gdef'][n] = gds
                            if txt: sp['active_gtext'][n] = [f'Active: {t}' for t in txt]
                            off, gds, txt = gear_spec(u, u['passive'] or {}, (prow or {}).get('Gear'), lv, trig,
                                                      (prow or {}).get('Ability_Text', ''))
                            if off: sp['passive_goff'][n] = off
                            if gds: sp['passive_gdef'][n] = gds
                            if txt: sp['passive_gtext'][n] = [f'Passive: {t}' for t in txt]
                            if RELICS and u['relic']:
                                # the relic's effect: always on, like a passive (relic level RELIC_LEVEL)
                                rrow, rab = relics.get(u['relic']['name']), u['relic']['ability'] or {}
                                rtext = []
                                if (x := attack_spec(u, rrow, RELIC_LEVEL, trig, rab)):
                                    old = sp['passive'].get(n) or ([], [])
                                    sp['passive'][n] = (old[0] + x[0], old[1] + x[1])
                                    rtext += x[1]
                                if (x := defence_spec(u, rab, (rrow or {}).get('Defence'), RELIC_LEVEL, trig)):
                                    sp['passive_def'][n] = merge_defence(sp['passive_def'].get(n), x)
                                    rtext += x['text']
                                off, gds, txt = gear_spec(u, rab, (rrow or {}).get('Gear'), RELIC_LEVEL, trig,
                                                          (rrow or {}).get('Ability_Text', ''))
                                if off: sp['passive_goff'][n] = (sp['passive_goff'].get(n) or []) + off
                                if gds: sp['passive_gdef'][n] = merge_defence(sp['passive_gdef'].get(n), gds)
                                rtext += txt
                                if rtext: sp['relic_text'][n] = rtext
                    except (ValueError, KeyError, IndexError) as e:
                        sys.exit(f'{n}: can\'t read its ability row ({e}). Check the tokens in the ability CSVs.')
                specs[(lv, trig, gear)] = sp
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--creed', help='path to the Castellan Creed test CSV, to re-check the model')
    args = ap.parse_args()
    set_tier(TIERS[1])
    g, units = load()
    actives = sync_rows(ACTIVES_CSV, ACTIVE_COLS, 'Active', units, draft_active, 'active_abilities.csv')
    passives = sync_rows(PASSIVES_CSV, PASSIVE_COLS, 'Passive', units, draft_passive, 'passive_abilities.csv')
    relics = sync_relics(g, units)
    per_tier, rows, tables = {}, [], {}
    for t in TIERS:
        set_tier(t)
        g, units = load()
        specs = build_specs(units, actives, passives, relics)
        tables[t['key']] = {}
        res = run_scenarios(units, specs, tables[t['key']])
        per_tier[t['key']] = tier_html(units, res, specs)
        rows += tier_rows(units, res, actives, passives, specs)
        print(f"  {t['label']}: done")
    write_stats(rows, g['version'])
    write_html(units, per_tier, actives, passives, relics, g['version'])
    write_typical(units, tables, g['version'])
    print(f'Built roster-battle-map.html, typical-character.html and tacticus_stats.csv: {len(units)} characters x {len(TIERS)} tiers, '
          f'game version {g["version"]}.')
    if args.creed:
        set_tier(TIERS[1])
        g, units = load()
        creed_check(args.creed, units)


if __name__ == '__main__':
    main()
