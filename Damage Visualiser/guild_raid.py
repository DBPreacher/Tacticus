"""
guild_raid.py - the best 5 characters for a Guild Raid boss (work in progress).

A Guild Raid attack is 6 turns against one boss with up to 5 characters, and you can't use the boss's own
faction. This works out how much damage a team does in those 6 turns, using build_map.py's damage model
and the Attack-side buffs in support_abilities.csv, then searches for the best five.

Rules from the game data (see INSTRUCTIONS.md, "Guild Raid"):
- Bosses are Immune: Armour, hits, Movement and Range can't be reduced, and they can't be Stunned,
  Suppressed or Taunted. Armour-reduction buffs are dropped; "+Damage taken" buffs still count.
- Bosses block (blockChance / blockDamage), are Big Targets, and have their own Armour and Health.
- Side battles: winning them applies a chain of debuffs to the boss. The switch applies both chains in
  full (mostly -30% Armour and -15% block chance).
- Each character attacks once a turn and uses its active once, on turn 1. Some actives don't end the
  turn, so those characters attack that turn as well (the model's opener handles it).
- Not counted yet: the boss killing your characters, summons, terrain height, bombs.

    python -X utf8 guild_raid.py --boss "Belisarius Cawl" [--debuffs] [--gear] [--ability 50] [--tier mythic]
"""
import argparse, csv, json, os, re
import build_map as bm
import support_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
TURNS = 6
TEAM = 5
TEAM_REACH = {'team': 4, 'target': 4, 'one': 1, 'next attack': 1, 'adjacent': 2, '2 hexes': 3}   # of the 4 team-mates
FACTION_ID = {'AdeptusMechanicus': 'Adeptus Mechanicus', 'Orks': 'Orks', 'Tyranids': 'Tyranids', 'Aeldari': 'Aeldari',
              'AstraMilitarum': 'Astra Militarum', 'Tau': 'Tau Empire', 'ThousandSons': 'Thousand Sons',
              'DeathGuard': 'Death Guard', 'DarkAngels': 'Dark Angels', 'Necrons': 'Necrons'}


def game():
    with open(os.path.join(HERE, 'cache', 'gameinfo.json'), encoding='utf-8') as f:
        return json.load(f)


def fights(g):
    """every boss fight in the season configs: one row per boss and level"""
    out, seen = [], set()
    for s in g['guildBossSeasons']:
        for stt in s['sets']:
            enc = [e for e in stt['encounters'] if e['guildBossEncounterType'] == 'Boss'][0]
            uid, lvl = enc['unitId'].split(':')
            if (uid, int(lvl)) in seen:
                continue
            seen.add((uid, int(lvl)))
            u = g['guildRaidUnits'][uid]
            stats = u['stats'][min(int(lvl), len(u['stats']) - 1)]
            out.append(dict(season=s['name'], tier=stt['tier'], set=stt['set'], uid=uid, level=int(lvl),
                            name=u['name'], faction=u['factionId'], rarity=stats['baseRarity'], hp=stats['health'],
                            bossType=enc['bossType'], minis=[e['unitId'].split(':')[0] for e in stt['encounters'][1:]]))
    return sorted(out, key=lambda f: f['hp'])


def debuff_totals(g, fight):
    """what winning both side battles takes off this boss (each chain in full). Most steps weaken the
    boss's attacks or its summons, which this tool doesn't model, but some weaken the rules that decide
    how much damage it takes: Mortarion's Revoltingly Resilient and the Lion's Emperor's Shield."""
    tot = dict(armour=0.0, block=0.0, steps=0, res_hits=0, no_shield=False)
    for k, chain in g['bossDebuffs'].items():          # each chain once, even when both side battles are the same unit
        for mini in set(fight['minis']):
            if not k.startswith(mini + '_'):
                continue
            suffix = k[len(mini) + 1:].lstrip('0123456789')      # some chains name the boss, some don't
            if suffix and fight['bossType'].lower() not in suffix.lower():
                continue
            for x in chain:
                tot['steps'] += 1
                if 'fixedArmor' in x:
                    tot['armour'] += int(x.rsplit('_', 1)[1])
                elif 'blockChance' in x:
                    tot['block'] += int(x.rsplit('_', 1)[1])
                elif 'RevoltinglyResilient_hits' in x:
                    tot['res_hits'] += int(x.rsplit('_', 1)[1])      # another hit lands in full
                elif x.endswith('TheEmperorsShield'):
                    tot['no_shield'] = True                          # the Lion stops building up block
            break
    return tot


def boss_defender(g, fight, debuffs=False):
    """the boss as the damage model's defender, plus a defence spec for its block"""
    u = g['guildRaidUnits'][fight['uid']]
    s = u['stats'][min(fight['level'], len(u['stats']) - 1)]
    d = debuff_totals(g, fight) if debuffs else dict(armour=0.0, block=0.0, steps=0)
    boss = dict(name=u['name'], hp=s['health'], arm=s['fixedArmor'] * max(1 - d['armour'] / 100, 0.0),
                dmg=s['damage'], traits=set(u['traits']), weapons=[], g=None)
    ds = bm.new_ds()
    ds['bc'] = max((s['blockChance'] or 0) - d['block'], 0) / 100
    ds['bd'] = float(s['blockDamage'] or 0)
    return boss, ds, d


def boss_rules(g, fight, dbf=None):
    """the boss passives that change how much damage it takes, read from the game data at its ability level,
    and what clearing the side battles does to them. Everything else about a boss (its own attacks, summons,
    what you can dodge, the bosses that repair themselves) isn't modelled yet."""
    u = g['guildRaidUnits'][fight['uid']]
    lvl = u['stats'][min(fight['level'], len(u['stats']) - 1)]['abilityLevel']
    out = dict(diminish=None, psyker_pct=0.0, block_ramp=0.0, charge_hits=0, notes=[])

    def const(k, name, default=0.0):
        a = g['abilities'].get(k) or {}
        v = (a.get('constants') or {}).get(name)
        if v is None:
            var = (a.get('variables') or {}).get(name)
            v = var[min(lvl - 1, len(var) - 1)] if var else default
        return float(v)
    for k in (u.get('passiveAbilities') or []) + (u.get('activeAbilities') or []):
        if k == 'RevoltinglyResilient':                 # Mortarion: hits after the first get halved, then halved again
            out['diminish'] = (int(const(k, 'nrOfHits', 1)), const(k, 'dmgPctReduction', 50))
            n_ = out['diminish'][0]
            out['notes'].append(f"only the first {'hit' if n_ == 1 else str(n_) + ' hits'} of an attack lands in "
                                f"full, each one after that {out['diminish'][1]:.0f}% weaker than the last")
        elif k == 'NoctilithBeacons':                   # Szarekh: Psykers do less
            out['psyker_pct'] = const(k, 'dmgPctReduction', 0)
            out['notes'].append(f"Psykers deal -{out['psyker_pct']:.0f}% damage")
        elif k == 'TheEmperorsShield':                  # Lion: melee hits give him block for the turn
            out['block_ramp'] = const(k, 'blockChance', 0)
            out['notes'].append(f"every melee hit gives +{out['block_ramp']:.0f}% block chance for the turn, "
                                "and he hits back at attacks he blocks twice")
        elif k == 'ObeisanceGenerators':                # Szarekh: don't charge him
            out['charge_hits'] = int(const(k, 'hitsReduction', 0))
            out['notes'].append(f"charging him costs you {out['charge_hits']} hits, so stand still and attack")
    if dbf and dbf.get('res_hits') and out['diminish']:
        n_ = out['diminish'][0] + dbf['res_hits']
        out['diminish'] = (n_, out['diminish'][1])
        out['notes'] = [f"the side battles bought you {dbf['res_hits']} more hits: the first {n_} hits of an "
                        f"attack land in full, each one after that {out['diminish'][1]:.0f}% weaker"
                        if 'land' in x or 'lands' in x else x for x in out['notes']]
    if dbf and dbf.get('no_shield') and out['block_ramp']:
        out['block_ramp'] = 0.0
        out['notes'] = [("the side battles took the Emperor's Shield away: no block building up"
                         if 'block chance for the turn' in x else x) for x in out['notes']]
    return out


def hits_of(a, w):
    """how many hits one attack scores, for the boss rules that count hits. The hits a passive adds come
    in a separate attack (Kharn's second attack, Kariyan's Legacy of Combat), so a rule like Mortarion's
    'only the first hits land in full' starts again for those and they are not counted here."""
    n = w['hits']
    for e in (a.get('ps') or ([], []))[0]:
        if e['kind'] == 'hits' and e['scope'] in ('all', w['kind']):
            n += e['value']
    return max(n, 1)


def rule_factor(a, w, rules, member):
    """what the boss's rules do to one attack: a share of the damage that still lands"""
    f = 1.0
    if rules['diminish']:
        first, pct = rules['diminish']
        n, keep, step = hits_of(a, w), 0.0, 1.0
        for i in range(1, int(round(n)) + 1):
            if i <= first:
                keep += 1.0
            else:
                step *= 1 - pct / 100
                keep += step
        f *= keep / n
    if rules['psyker_pct'] and 'Psyker' in member['traits']:
        f *= 1 - rules['psyker_pct'] / 100
    if rules['block_ramp'] and w['kind'] == 'melee':
        # his block chance climbs with each hit landed this turn: the middle of the climb, over the team's attacks
        n = hits_of(a, w)
        f *= max(1 - min(rules['block_ramp'] / 100 * n / 2, 0.6), 0.4)
    return f


def setting(tier_key, lv, trig, act, gear):
    """the roster at one of the map's settings, with its ability specs"""
    t = next(x for x in bm.TIERS if x['key'] == tier_key)
    bm.set_tier(t)
    g, units = bm.load()

    def rd(path, k):
        with open(path, newline='', encoding='utf-8') as f:
            return {r[k]: r for r in csv.DictReader(f)}
    specs = bm.build_specs(units, rd(bm.ACTIVES_CSV, 'Name'), rd(bm.PASSIVES_CSV, 'Name'), rd(bm.RELICS_CSV, 'Relic'))
    U, sp, rnd, rest = sm.setting_units(units, specs, lv, trig, act, gear)
    return U, sp, rnd, rest


def buff_turns(r, ab):
    """how many of the 6 turns a buff is up. A passive is up all battle unless it names a shorter window.
    An active starts on turn 1 and comes back whenever its cooldown allows, so a 2-round buff on a 2-turn
    cooldown covers 4 of the 6 turns."""
    lasts = (r['Lasts'] or '').strip().lower()
    active = r['Source'] == 'Active'          # the Condition column is a switch, not a duration
    if lasts == 'battle':
        return TURNS
    if lasts == 'once':
        return 1                                        # it only ever happens once
    m = re.match(r'(\d+)\s*round', lasts)
    rounds = int(m.group(1)) if m else 1
    if not active:
        if lasts.startswith('each') or lasts in ('turn', 'every turn', ''):
            return TURNS                                # something that happens again every turn
        if lasts == 'every third round':
            return -(-TURNS // 3)
        return min(rounds, TURNS)
    cd = (ab.get('constants') or {}).get('cooldownTurns') if ab else None
    cd = int(float(cd)) if cd not in (None, '') else 2
    uses = (TURNS - 1) // (cd + 1) + 1                  # turn 1, then every cooldown + 1 turns
    return min(TURNS, rounds * uses)


def buffs_for(member, mates, rows, lv, trig, act, immune):
    """the Attack-side tokens this member picks up from its team-mates, each with how many of the 6 turns
    it is up. Each buff goes to the team-mates it helps most (biggest Damage first), as far as its reach
    allows."""
    toks = []
    everyone = mates + [member]
    lookup = {u['name']: u for u in everyone}
    for s in mates:
        for r in rows:
            if r['Name'] != s['name'] or r['Source'] == 'Relic':
                continue
            if (r['Source'] == 'Active' or r['Condition'] == 'active') and not act:
                continue
            if r['Condition'] == 'trig' and not trig:
                continue
            if immune and r['Name'] == 'Xybia' and r['Ability'] == 'Mind Control':
                continue      # Mind Control needs the Taunt to land, and a Boss is immune to Taunt
            if not sm.matches(member, r['Receives']):
                continue
            eligible = [m for m in everyone if m['name'] != s['name'] and sm.matches(m, r['Receives'])]
            eligible.sort(key=lambda m: -m['dmg'])
            if member['name'] not in [m['name'] for m in eligible[:TEAM_REACH.get(r['Reach'], 1)]]:
                continue
            ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(lookup, r)
            up = buff_turns(r, ab)
            for t in sm.tokens_for(r, member, ab, relic, lv, trig):
                if immune and t['kind'] == 'armour':          # a Boss's Armour can't be reduced
                    continue
                toks.append((t, up))
    return toks


# actives that grow as the battle goes on. RAMP: +pct for every turn its owner has already fought
# (Kariyan's Martial Inspiration). RAMP_FLAT: +Damage for every active the team has used so far
# (Atlacoya's Talons Of The Emperor). Both are worth more the later they go off, so the model holds them.
HIGH_GROUND_PCT = 50      # the wiki: a unit on high ground deals +50% Damage to one below it
HIGH_GROUND = 2           # how many of the five stand on it when the High ground switch is on. Watching
                          # real runs, the two biggest hitters take the high ground (owner, Sept 2026)
RAMP = {'Kariyan': 'extraDmgPct'}
RAMP_FLAT = {'Atlacoya': 'extraDmg'}
# Talons Of The Emperor is Direct Damage - no Armour at all - against a Psyker, or next to a Custodes
DIRECT = {'Atlacoya': ('Psyker', 'Adeptus Custodes')}
# an active that scores a hit for every Psychic attack the team makes that turn (Sekhetar's Warpflamer)
PSYCHIC_HITS = {'Sekhetar': 'maxNrOfHits'}


def active_turns(member, turns):
    """the turns a character gets its active off. Nearly every active is once a battle: only the few with a
    cooldownTurns in the data come back (Baraqiel, Ramus, Aesoth, Tyrith, Kariyan). An active that grows
    is held back as late as it can be without losing a use."""
    c = ((member.get('ability') or {}).get('constants') or {}).get('cooldownTurns')
    late = member['name'] in RAMP or member['name'] in RAMP_FLAT
    if c in (None, ''):
        return {turns if late else 1}
    step = int(float(c)) + 1
    return set(range(turns, 0, -step)) if late else set(range(1, turns + 1, step))


def ramp_at(member, turn, lv):
    """what an active that grows each turn is worth on this turn: +pct for every turn already fought"""
    var = RAMP.get(member['name'])
    if not var or turn <= 1:
        return 1.0
    return 1 + sm.value(member['ability'] or {}, var, lv) / 100 * (turn - 1)


def tweak_spec(member, spec, team, boss, turn, lv, used):
    """the parts of an active that change with the battle: Atlacoya's grows with every active the team has
    used and turns Direct next to a Custodes or against a Psyker"""
    if not spec or not spec.get('parts'):
        return spec
    var, direct = RAMP_FLAT.get(member['name']), DIRECT.get(member['name'])
    psy = PSYCHIC_HITS.get(member['name'])
    if not var and not direct and not psy:
        return spec
    parts = [dict(p) for p in spec['parts']]
    if psy:
        # one more hit for each team-mate whose attack deals Psychic damage, up to the ability's cap
        n = sum(1 for m in team if m['name'] != member['name']
                and any(w['type'] in ('Psychic', 'Direct') for w in m['weapons']))
        cap = float(((member['ability'] or {}).get('constants') or {}).get(psy) or 99)
        for p in parts:
            p['hits'] = int(min(p['hits'] + n, cap))
    if var:
        add = sm.value(member['ability'] or {}, var, lv) * used
        for p in parts:
            p['dmg'] += add
    if direct:
        trait, faction = direct
        if trait in boss['traits'] or any(m['faction'] == faction for m in team if m['name'] != member['name']):
            for p in parts:
                p['type'] = 'Direct'
    return dict(spec, parts=parts)


def member_damage(member, mates, boss, ds, rows, sp, lv, trig, act, gear, rules=None, extra=None, turns=TURNS,
                  mow=None, team_uses=(), high=False):
    """one character's damage over the 6 turns: the active turn plus normal attacks.
    extra: flat Damage added to this character's stat (Laviscus's Outrage, the Neurothrope's parasite).
    turns: how many of the 6 it is alive for, when the deaths switch is on.
    extra: flat Damage, or (first turn, later turns) when it changes after the opening turn."""
    rules = rules or dict(diminish=None, psyker_pct=0.0, block_ramp=0.0, charge_hits=0, notes=[])
    if turns <= 0:
        return 0.0
    toks = buffs_for(member, mates, rows, lv, trig, act, 'Immune' in boss['traits'])
    spec = sp['active'].get(member['name']) if act else None

    chaos = sum(1 for m in mates if m['alliance'] == 'Chaos') if member['name'] == 'Laviscus' else 0

    def attack(live, xtra, turn=1):
        """(the damage of one normal attack, the damage of a turn it gets its active off)"""
        used = sum(1 for x in team_uses if x < turn)
        spec1 = tweak_spec(member, spec, [member] + mates, boss, turn, lv, used)
        a, spec2, _ = sm.buffed(member, live, spec1, gear) if live else (member, spec1, 0.0)
        if xtra:
            a = dict(a, dmg=a['dmg'] + xtra)
        if high:                                     # high ground lifts the whole Damage stat, Outrage and all
            a = dict(a, dmg=a['dmg'] * (1 + HIGH_GROUND_PCT / 100))
        if chaos:                                       # Refusal to be Outdone's other half
            cd = sm.value(member['passive'] or {}, 'extraCritDmg', lv) * chaos
            a = dict(a, pg=list(a.get('pg') or []) +
                     [dict(kind='critdmg', value=cd, scope='all', vs=None, vsnot=None)])

        dmg, _, w = bm.best_attack(a, boss, trig, ds, False, False)
        f = rule_factor(a, w, rules, member)
        if mow and mow['kind'] == 'taken' and (not mow['only'] or mow['only'] == w['kind']):
            f *= 1 + mow['pct'] / 100                   # the boss takes more damage from these attacks
        first = sum(x[0] for x in bm.opener(a, boss, trig, spec2, ds)) * f if spec2 else 0.0
        return dmg * f, first
    # the turns fall into blocks: as each short buff runs out, work out the attack again
    ups = sorted({min(up, turns) for _, up in toks} | {turns})
    actives = active_turns(member, turns) if act else set()
    x1, x2 = extra if isinstance(extra, tuple) else (extra, extra)
    total, done = 0.0, 0
    for up in ups:
        live = [t for t, n in toks if n > done]
        normal, first = attack(live, x2)
        n1, f1 = attack(live, x1) if x1 != x2 else (normal, first)
        grows = member['name'] in RAMP or member['name'] in RAMP_FLAT
        for turn in range(done + 1, up + 1):
            nm, fs = (n1, f1) if turn == 1 else (normal, first)
            if fs and turn in actives:
                if grows:                               # work the opener out again for this turn
                    nm2, fs = attack(live, x1 if turn == 1 else x2, turn)
                    nm = nm2 if turn == 1 else nm
                total += max(fs * ramp_at(member, turn, lv), nm)
            else:
                total += nm
        done = up
    return total


_BIG = {}                 # biggest_hit is the hot path in a search, and the same five come round again


def biggest_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear, opener=False):
    key = (member['name'], tuple(sorted(m['name'] for m in mates)), opener, boss['name'], round(boss['arm']),
           round(ds['bc'] * 100) if ds else 0, lv, trig, act, gear)
    if key in _BIG:
        return _BIG[key]
    _BIG[key] = v = _biggest_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear, opener)
    if len(_BIG) > 400000:
        _BIG.clear()
    return v


def _biggest_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear, opener=False):
    """this character's biggest single non-Psychic hit on the boss in a turn - what Laviscus's Outrage
    feeds on. It is the biggest *hit*, not the biggest attack, so the hits a passive adds count (Kariyan's
    Legacy of Combat lands one big Piercing hit on a Big Target) and so do the parts of an active on the
    turn it is used (opener=True)."""
    toks = [t for t, _ in buffs_for(member, mates, rows, lv, trig, act, 'Immune' in boss['traits'])]
    spec = sp['active'].get(member['name']) if (act and opener) else None
    if spec:            # the turn it goes off, an active that grows is at its biggest
        spec = tweak_spec(member, spec, [member] + mates, boss, TURNS, lv, len(mates))
    a, spec2, _ = sm.buffed(member, toks, spec, gear) if toks else (member, spec, 0.0)
    best = 0.0
    # "the highest damage dealt by any of their non-Psychic hits": across an attack's hits that is usually
    # a crit, so this weighs the crit hit by the chance at least one of the hits crits (wiki, HDTW Outdone)
    crit = (a.get('g') or {}).get('cc') or 0.0
    # the weapon attack on its own: the hits a passive adds come in their own attack and are weighed below,
    # so they must not be mixed into this average
    eff, desc = (a.get('ps') or ([], []))
    plain = dict(a, ps=([e for e in eff if e['kind'] not in ('extra', 'extrahalf')], desc))
    for w in plain['weapons']:
        if w['type'] in ('Psychic',):              # Outrage only counts non-Psychic hits
            continue
        n = max(hits_of(plain, w), 1)
        avg = bm.best_attack(plain, boss, trig, ds, False, False, w['kind'])[0] / n
        if crit:
            ac = dict(plain, g=dict(plain['g'], cc=1.0))
            hot = bm.best_attack(ac, boss, trig, ds, False, False, w['kind'])[0] / n
            p = 1 - (1 - crit) ** n                # the chance at least one hit crits
            avg = p * hot + (1 - p) * avg
        best = max(best, avg)
    parts = [(e['part_big'] if (e.get('part_big') and 'BigTarget' in boss['traits']) else e['part'])
             for e in (a.get('ps') or ([], []))[0] if e['kind'] in ('extra', 'extrahalf')]
    if spec2:
        parts += spec2.get('parts') or []
    for p in parts:
        if p['type'] in ('Psychic',):
            continue
        # the same way the model works out ability damage anywhere else: the boss's defence and crits
        best = max(best, bm.part_vs_defence(p, boss, ds, False, a, trig)[0] / max(p['hits'], 1))
    return best


def ability_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear):
    """the biggest hit of this character's own active, for the turn it uses it"""
    spec = sp['active'].get(member['name'])
    if not spec or not spec.get('parts'):
        return 0.0
    return max((bm.part_vs_defence(p, boss, ds, False, member, trig)[0] / max(p['hits'], 1)
                for p in spec['parts'] if p['type'] not in ('Psychic',)), default=0.0)


def outrage(member, team, boss, ds, rows, sp, lv, trig, act, gear):
    """Laviscus, at face value: every friendly character attacking the boss next to him adds its biggest
    non-Psychic hit to his Outrage, and his Damage goes up by 120% of it. It resets when he attacks, so
    this is what he has each turn. (the first turn, when the others get their actives off, then the rest)"""
    mates = [x for x in team if x['name'] != member['name']]
    pct = sm.value(member['passive'], 'extraDmgPct', lv) / 100
    each = lambda opener: pct * sum(
        biggest_hit(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp, lv, trig, act, gear, opener)
        for m in mates)
    # his own Euphoric Strikes doesn't end his turn, so it feeds his Outrage before he attacks (wiki)
    own = pct * ability_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear) if act else 0.0
    return (each(True) + own, each(False))


def parasite(member, team, boss, lv, gear, tier_key):
    """the Neurothrope's Neuroparasite: his Psychic damage grows by extraDmg for each level, and a level
    goes on every time the boss takes Psychic damage. With a Psyker team it reaches the cap quickly, so
    this counts the cap, and the Norn Crown's bonus for the other Psykers at Mythic."""
    neuro = next((m for m in team if m['name'] == 'Neurothrope'), None)
    if not neuro:
        return 0.0
    ab = neuro['passive'] or {}
    cap = float((ab.get('constants') or {}).get('buffMaxLevel') or (ab.get('variables') or {}).get('buffMaxLevel', [15])[0])
    if member['name'] == 'Neurothrope':
        return sm.value(ab, 'extraDmg', lv) * cap
    # Norn Crown (Mythic, gear on): the other Psykers also hit an infected enemy harder
    if 'Psyker' in member['traits'] and tier_key == 'mythic' and gear and (neuro.get('relic') or {}).get('name') == 'Norn Crown':
        return sm.value(neuro['relic']['ability'], 'extraDmg', bm.RELIC_LEVEL, True)
    return 0.0


# ---------------------------------------------------------------- what the boss does back
# What each boss puts on your characters in an enemy turn, read from its own abilities. 'front' = every
# character standing next to it (it is a Big Target, so that is everyone attacking in melee), 'one' = a
# single attack shared over the front line. rate = how often it comes round (1 / (cooldown + 1)).
# Telegraphed attacks you can walk out of (Szarekh's Annihilator Beam, the Lion's Instruments of
# Vengeance) are left out, and so are the summons.
PRESSURE = {
    'GuildBoss5Boss1DeathMortarion': [
        dict(ab='ArchContaminator', where='front', rate=1.0, hp_pct=('extraDmgPct', 'extraDmgPct_2')),
        dict(ab='ReapingScythe', where='front', rate=0.5),
        dict(weapon='melee', where='one', rate=0.5),
    ],
    'GuildBoss3Boss1NecroSilentKing': [
        dict(weapon='melee', where='one', rate=1.0),
    ],
    'GuildBoss12Boss1DarkaLion': [
        dict(ab='Fealty', where='front', rate=1.0),
        dict(ab='MartialExemplar', where='front', rate=1.0 / 3),
        dict(ab='TheLionsWrath', where='one', rate=0.5, parts=('1', '2')),
        dict(weapon='melee', where='one', rate=1.0),
    ],
}


def bossval(ab, key, lv):
    """a boss ability value. Not bm.ability_value: that adds the roster's rarity bonus, which is a
    character thing - a boss's numbers are what the data says."""
    v = (ab.get('variables') or {}).get(key)
    if v is None:
        c = (ab.get('constants') or {}).get(key)
        return float(c) if c not in (None, '') else None
    return float(v[min(int(lv), len(v)) - 1])


def _part(ab, lv, s='', dtype=None):
    """one damage part of a boss or Machine of War ability: its average damage, its hits and its damage
    type. dtype: for the few abilities whose type is only in their text (the Biovore's Spore Mines)"""
    suf = '' if s in ('', '1') else '_' + s
    lo, hi = bossval(ab, 'minDmg' + suf, lv), bossval(ab, 'maxDmg' + suf, lv)
    c = ab.get('constants') or {}
    return dict(dmg=(lo + hi) / 2, hits=int(float(c.get('nrOfHits' + suf) or c.get('nrOfHits') or 1)),
                type=bm.dtype(dtype or c.get('damageProfile' + suf) or c.get('damageProfile') or 'Physical'),
                crit=False)


def pressure(g, fight):
    """the terms of one enemy turn: what the boss puts out and who stands in it"""
    u = g['guildRaidUnits'][fight['uid']]
    st = u['stats'][min(fight['level'], len(u['stats']) - 1)]
    lv = int(st.get('abilityLevel') or 50)
    out = []
    for spec in PRESSURE.get(fight['uid'], [dict(weapon='melee', where='one', rate=1.0)]):
        if spec.get('weapon'):
            w = u['meleeWeapon'] if spec['weapon'] == 'melee' else u['rangeWeapon']
            parts = [dict(dmg=st['damage'], hits=w['hits'], type=bm.dtype(w['damageProfile']), crit=False)]
            name = 'normal ' + spec['weapon'] + ' attack'
        else:
            ab = g['abilities'][spec['ab']]
            parts = [_part(ab, lv, s) for s in spec.get('parts', ('1',))]
            name = ab.get('name') or spec['ab']
        hp_pct = 0.0
        if spec.get('hp_pct'):
            vals = [bossval(g['abilities'][spec['ab']], k, lv) for k in spec['hp_pct']]
            hp_pct = sum(vals) / len(vals)
        for i, p in enumerate(parts):
            out.append(dict(part=p, hp_pct=hp_pct if i == 0 else 0.0, where=spec['where'],
                            rate=spec['rate'], name=name))
    return out


def team_defence(member, mates, drows, lv, trig, act, gear, tier_key):
    """the Defence-side buffs this character picks up from its team-mates: (first enemy turn, later, regen)"""
    first, later = bm.new_ds(), bm.new_ds()
    regen = dict(turn=0.0, hit=0.0, shield=0.0, shield_first=0.0)
    everyone = mates + [member]
    lookup = {u['name']: u for u in everyone}
    for s in mates:
        for r in drows:
            if r['Name'] != s['name']:
                continue
            if (r['Source'] == 'Active' or r['Condition'] == 'active') and not act:
                continue
            if r['Condition'] == 'trig' and not trig:
                continue
            if r['Source'] == 'Relic' and not (tier_key == 'mythic' and gear):
                continue
            if not sm.matches(member, r['Receives']):
                continue
            eligible = [m for m in everyone if m['name'] != s['name'] and sm.matches(m, r['Receives'])]
            eligible.sort(key=lambda m: -m['dmg'])          # the team stands around its damage dealers
            if member['name'] not in [m['name'] for m in eligible[:TEAM_REACH.get(r['Reach'], 1)]]:
                continue
            ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(lookup, r)
            got = sm.defence_for(r, s, member, ab, relic, lv, trig)
            if not got:
                continue
            ds1, ds2, rg, _ = got
            first, later = bm.merge_defence(first, ds1), bm.merge_defence(later, ds2)
            for k in regen:
                regen[k] += (rg or {}).get(k, 0.0)
    return first, later, regen


def in_melee(m):
    """does this character have to stand next to the boss to do its damage?"""
    return (max(m['weapons'], key=lambda w: w['hits'])['kind'] == 'melee'
            or all(w['kind'] == 'melee' for w in m['weapons']))


def front_line(team):
    """how many of the five stand next to the boss"""
    return max(sum(1 for m in team if in_melee(m)), 1)


_SURV = {}


def survives(member, mates, terms, front, drows, lv, trig, act, gear, tier_key, own=(None, None)):
    """how many of the 6 turns this character gets to attack in before the boss kills it. Characters that
    fight in melee stand next to the boss and take everything it puts out there; the rest keep their
    distance and only take its single attacks."""
    key = (member['name'], tuple(sorted(m['name'] for m in mates)), front)
    if key in _SURV:
        return _SURV[key]
    ds1, ds2, regen = team_defence(member, mates, drows, lv, trig, act, gear, tier_key)
    ds1 = bm.merge_defence(own[0], ds1) or ds1                  # its own defensive passives and actives
    ds2 = bm.merge_defence(own[1], ds2) or ds2
    d1, d2 = bm._with_defence(member, ds1), bm._with_defence(member, ds2)
    pool = member['hp'] * ds1['hpmult'] + ds1['heal'] + regen['shield_first'] + regen['shield']
    melee = in_melee(member)
    turns = TURNS
    for turn in range(1, TURNS + 1):
        d, dsx = (d1, ds1) if turn == 1 else (d2, ds2)
        took = 0.0
        for t in terms:
            if t['where'] == 'front' and not melee:
                continue
            share = 1.0 / max(front, 1) if t['where'] == 'one' else 1.0
            took += bm.part_vs_defence(t['part'], d, dsx, turn == 1)[0] * t['rate'] * share
            took += member['hp'] * t['hp_pct'] / 100 * t['rate'] * share
        pool -= took
        pool += regen['turn'] + (regen['shield'] if turn > 1 else 0.0)
        if pool <= 0:
            turns = turn                                    # it attacked this turn, then died
            break
    _SURV[key] = turns
    return turns


# ---------------------------------------------------------------- the Machine of War slot
# A raid team is five characters plus a Machine of War, and every Machine of War has a Mythic ability
# that works on friendly Mythic characters. That ability is the reason one of them is in every team:
# 'taken' = the boss takes more damage, 'dmg' = your characters hit harder. only= restricts it to melee
# or ranged attacks, who= to a trait. The conditions are all things the Machine of War sets up itself
# (the Biovore's Spore Mines, the Plagueburst Crawler's contaminated hexes), so they are counted as on.
MOW_BUFF = {
    'Biovore': dict(kind='taken', ab='HyperCorrosiveAcid', note='everything a Spore Mine has hit'),
    'Rukkatrukk': dict(kind='taken', ab='MoreGitzOverEre', only='melee', note='normal melee attacks only'),
    'Malleus Rocket Launcher': dict(kind='taken', ab='OnMyPosition', only='ranged', note='ranged attacks only'),
    'Reanimator': dict(kind='dmg', ab='GuardianConstruct', who='Mechanical', note='Mechanical characters only'),
    "Z'Kar": dict(kind='dmg', ab='CabalOfSorcerers', who='Psyker', note='Psyker characters only'),
    # Blighted Land needs your characters to stand on the hexes it contaminates, so it follows the
    # Traits switch, like the other effects you have to set up. The rest are things the machine does itself.
    'Plagueburst Crawler': dict(kind='dmg', ab='BlightedLand', note='on a contaminated hex', trig=True),
    # the rest are defensive (less damage taken, shields): nothing for a damage run
    'Galatian': None, 'Exorcist': None, 'Forgefiend': None, "Tson'ji": None, 'Storm Speeder': None,
}
MOW_SHOTS = {      # what it can fire at a boss, how often, and its damage type when the data leaves it out
    'Biovore': [('SporeMineLauncher', 1.0, 'Toxic')],   # a Spore Mine every turn, walked into the boss
    'Galatian': [('MacroPlasmaIncinerator', 0.5)],
    'Exorcist': [('DevastatingRefrain', 0.5)],
    'Reanimator': [],                                   # repairs and summons, no attack of its own
    'Malleus Rocket Launcher': [('MalleusRocketBarrage', 0.5)],
    'Forgefiend': [('DaemonicOrdnance', 0.5)],          # the autocannons only fire at summons
    'Plagueburst Crawler': [('EntropyCannons', 1.0), ('PlagueburstMortar', 0.5)],
    'Rukkatrukk': [('SquigLaunchas', 0.5)],
    "Tson'ji": [('HeavyRailRifle', 0.5), ('TwinSmartMissileSystem', 0.5)],
    "Z'Kar": [('InfernalCannon', 0.5)],
    'Storm Speeder': [('DeathOnTheWind', 0.5)],
}
MOW_LEVELS = 65                   # a Machine of War's abilities go to 65
MYTHIC_ABILITY_LEVEL = 4          # its Mythic ability has four levels; the tool uses the top one


def machines(g):
    m = g['machinesOfWar']
    return list(m.values()) if isinstance(m, dict) else list(m)


def _ability(g, name):
    """a Machine of War ability by its id, or by the id its name normalises to"""
    ab = g['abilities'].get(name)
    if ab:
        return ab
    want = name.lower().replace("'", '')
    return next((a for k, a in g['abilities'].items()
                 if (a.get('name') or '').lower().replace(' ', '').replace("'", '').replace('-', '') == want), None)


def mow_buff(g, mow, lv, tier_key, trig=False):
    """what this Machine of War's Mythic ability does for the five (nothing below Mythic)"""
    spec = MOW_BUFF.get(mow['name'])
    if not spec or tier_key != 'mythic' or (spec.get('trig') and not trig):
        return None
    ab = _ability(g, spec['ab']) or next((g['abilities'][k] for k in (mow.get('mythicAbilities') or [])
                                          if k in g['abilities']), None)
    if not ab:
        return None
    pct = bossval(ab, 'extraDmgPct', MYTHIC_ABILITY_LEVEL) or 0.0
    return dict(kind=spec['kind'], pct=pct, only=spec.get('only'), who=spec.get('who', 'all'),
                name=ab.get('name') or spec['ab'], note=spec.get('note', ''))


def mow_damage(g, mow, boss, ds, lv, rules=None):
    """the Machine of War's own damage on the boss over the 6 turns"""
    tot = 0.0
    for shot in MOW_SHOTS.get(mow['name'], []):
        ab_id, rate, dt = (list(shot) + [None])[:3]
        ab = _ability(g, ab_id)
        if not ab or 'minDmg' not in (ab.get('variables') or {}):
            continue
        part = _part(ab, min(lv, MOW_LEVELS), '', dt)
        tot += bm.part_vs_defence(part, boss, ds, False)[0] * rate * TURNS
    return tot


def team_turns(team, surv, lv, trig, act, gear, tier_key):
    """{name: turns alive} for a team, or 6 each when the deaths switch is off"""
    if not surv:
        return {m['name']: TURNS for m in team}
    front = front_line(team)
    return {m['name']: survives(m, [x for x in team if x['name'] != m['name']], surv['terms'], front,
                                surv['drows'], lv, trig, act, gear, tier_key,
                                (surv['rnd'].get(m['name']), surv['rest'].get(m['name']))) for m in team}


def member_extra(m, team, boss, ds, rows, sp, lv, trig, act, gear, tier_key, buff):
    """the flat Damage a character brings into this team: Laviscus's Outrage, the Neuroparasite and the
    Norn Crown, a Machine of War's +Damage. (the first turn, then the rest)"""
    extra = outrage(m, team, boss, ds, rows, sp, lv, trig, act, gear) if m['name'] == 'Laviscus' else (0.0, 0.0)
    flat = parasite(m, team, boss, lv, gear, tier_key)
    if buff and buff['kind'] == 'dmg' and sm.matches(m, buff['who']):
        flat += m['dmg'] * buff['pct'] / 100
    return (extra[0] + flat, extra[1] + flat)


def high_ground(per_member):
    """who takes the high ground: the ones already doing the most damage, Outrage and all"""
    return set(sorted(per_member, key=per_member.get, reverse=True)[:HIGH_GROUND])


def team_damage(team, boss, ds, rows, sp, lv, trig, act, gear, rules=None, tier_key='d3', surv=None, mow=None,
                high=False):
    total = mow['own'] if mow else 0.0
    buff = mow['buff'] if mow else None
    alive = team_turns(team, surv, lv, trig, act, gear, tier_key)
    uses = sorted(x for m in team for x in (active_turns(m, TURNS) if act else ()))
    each, args = {}, {}
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra = member_extra(m, team, boss, ds, rows, sp, lv, trig, act, gear, tier_key, buff)
        each[m['name']] = member_damage(m, mates, boss, ds, rows, sp, lv, trig, act, gear, rules, extra,
                                        alive[m['name']], buff, uses)
        args[m['name']] = (m, mates, extra)
    if high:
        # the ones already doing the most damage take it, which is what the teams in the videos do
        for n in high_ground(each):
            m, mates, extra = args[n]
            each[n] = member_damage(m, mates, boss, ds, rows, sp, lv, trig, act, gear, rules, extra,
                                    alive[n], buff, uses, True)
    return total + sum(each.values())


def best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules=None, anchors=(), passes=3,
              tier_key='d3', surv=None, mow=None, high=False):
    """greedy five, then swap each slot for anything better until it stops improving.
    anchors: characters that must be in the team (the team styles the owner plays)."""
    pool = [u for u in U if u['faction'] != banned]
    names = lambda team: {u['name'] for u in team}
    score_of = lambda team: team_damage(team, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, surv,
                                        mow, high)
    team = [u for u in U if u['name'] in anchors]
    while len(team) < TEAM:
        team.append(max((u for u in pool if u['name'] not in names(team)), key=lambda u: score_of(team + [u])))
    score = score_of(team)
    for _ in range(passes):
        improved = False
        for i in range(TEAM):
            if team[i]['name'] in anchors:
                continue
            for u in pool:
                if u['name'] in names(team):
                    continue
                trial = team[:i] + [u] + team[i + 1:]
                s = score_of(trial)
                if s > score + 1:
                    team, score, improved = trial, s, True
        if not improved:
            break
    return team, score


def mow_options(g, fight, boss, ds, lv, tier_key, banned, trig=False):
    """every Machine of War you may bring to this boss, with its own damage and its Mythic ability"""
    out = []
    for m in machines(g):
        if FACTION_ID.get(m['factionId'], m['factionId']) == banned:
            continue                                    # the boss's own faction is banned here too
        out.append(dict(name=m['name'], faction=m['factionId'], own=mow_damage(g, m, boss, ds, lv),
                        buff=mow_buff(g, m, lv, tier_key, trig)))
    return out


def best_mow(team, opts, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, surv):
    """the Machine of War that adds the most to this team"""
    return max(opts, key=lambda mw: team_damage(team, boss, ds, rows, sp, lv, trig, act, gear,
                                                rules, tier_key, surv, mw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boss', default='Belisarius Cawl')
    ap.add_argument('--level', type=int, default=0, help='the fight level (0 = the hardest one for that boss)')
    ap.add_argument('--tier', default='d3')
    ap.add_argument('--ability', type=int, default=36)
    ap.add_argument('--gear', action='store_true')
    ap.add_argument('--trig', action='store_true')
    ap.add_argument('--no-active', action='store_true')
    ap.add_argument('--debuffs', action='store_true', help='both side battles cleared')
    ap.add_argument('--anchor', action='append', default=[], help='a character the team must include (repeatable)')
    ap.add_argument('--team', help='score this team instead of searching: comma-separated names')
    ap.add_argument('--deaths', action='store_true', help='count the boss killing your characters')
    ap.add_argument('--mow', help='the Machine of War to bring (default: the best one for the team)')
    ap.add_argument('--no-mow', action='store_true', help='no Machine of War slot')
    ap.add_argument('--high', action='store_true',
                    help=f'the {HIGH_GROUND} biggest hitters fight from high ground (+{HIGH_GROUND_PCT}%% Damage)')
    args = ap.parse_args()
    g = game()
    fs = [f for f in fights(g) if f['name'].lower().startswith(args.boss.lower())]
    fight = next((f for f in fs if f['level'] == args.level), fs[-1])
    boss, ds, dbf = boss_defender(g, fight, args.debuffs)
    rules = boss_rules(g, fight, dbf if args.debuffs else None)
    act = not args.no_active
    U, sp, rnd, rest = setting(args.tier, args.ability, args.trig, act, args.gear)
    rows = sm.load_rows('Attack')
    surv = dict(terms=pressure(g, fight), drows=sm.load_rows('Defence'), rnd=rnd, rest=rest) if args.deaths else None
    banned = FACTION_ID.get(fight['faction'], fight['faction'])
    print(f"{fight['name']} L{fight['level']} ({fight['rarity']}, tier {fight['tier']}): {fight['hp']:,} health, "
          f"{boss['arm']:,.0f} Armour, blocks {ds['bc'] * 100:.0f}% for {ds['bd']:,.0f}"
          + (f" · side battles cleared: -{dbf['armour']:.0f}% Armour, -{dbf['block']:.0f}% block" if args.debuffs else ''))
    for n in rules['notes']:
        print(f'   rule: {n}')
    print(f"no {banned} allowed · {TURNS} turns · {args.tier} abilities {args.ability} "
          f"{'standard gear' if args.gear else 'no gear'} {'all triggered' if args.trig else 'always-on'} "
          f"active {'on' if act else 'off'}"
          + (f" · {HIGH_GROUND} on high ground" if args.high else ''))
    opts = [] if args.no_mow else mow_options(g, fight, boss, ds, args.ability, args.tier, banned, args.trig)
    if args.mow:
        opts = [o for o in opts if o['name'].lower().startswith(args.mow.lower())]
    mow = None
    if args.team:
        want = [x.strip().lower() for x in args.team.split(',')]
        team = [u for u in U if u['name'].lower() in want]
        if opts:
            mow = best_mow(team, opts, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules, args.tier, surv)
        score = team_damage(team, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules, args.tier,
                            surv, mow, args.high)
    else:
        team, score = best_team(U, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, banned, rules,
                                tuple(args.anchor), tier_key=args.tier, surv=surv, high=args.high)
        if opts:
            mow = best_mow(team, opts, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules, args.tier, surv)
            team, score = best_team(U, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, banned, rules,
                                    tuple(args.anchor), tier_key=args.tier, surv=surv, mow=mow, high=args.high)
    print(f"\nBest five: {score:,.0f} damage in {TURNS} turns ({score / fight['hp'] * 100:.2f}% of the boss)")
    if mow:
        b = mow['buff']
        print(f"  Machine of War: {mow['name']} - {mow['own']:,.0f} damage of its own"
              + (f", and {b['name']} ({'the boss takes' if b['kind'] == 'taken' else 'your characters deal'} "
                 f"+{b['pct']:.0f}% - {b['note']})" if b else
                 (' (its Mythic ability only works on a Mythic roster)' if args.tier != 'mythic' else
                  ' (its Mythic ability needs All triggered)' if (MOW_BUFF.get(mow['name']) or {}).get('trig')
                  else ' (its Mythic ability is defensive: nothing for a damage run)')))
    alive = team_turns(team, surv, args.ability, args.trig, act, args.gear, args.tier)
    buff0 = mow['buff'] if mow else None
    uses0 = sorted(x for u in team for x in (active_turns(u, TURNS) if act else ()))
    extras = {m['name']: member_extra(m, team, boss, ds, rows, sp, args.ability, args.trig, act, args.gear,
                                      args.tier, buff0) for m in team}
    on_high = set()
    if args.high:
        plain = {m['name']: member_damage(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp,
                                          args.ability, args.trig, act, args.gear, rules, extras[m['name']],
                                          alive[m['name']], buff0, uses0) for m in team}
        on_high = high_ground(plain)
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra, buff = extras[m['name']], buff0
        alone = member_damage(m, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules)
        withteam = member_damage(m, mates, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules, extra,
                                 alive[m['name']], buff, uses0, args.high and m['name'] in on_high)
        tag = f'  (+{max(extra):,.0f} Damage from the team)' if max(extra) else ''
        if args.high and m['name'] in on_high:
            tag += '  [high ground]'
        if alive[m['name']] < TURNS:
            tag += f"  [dies on turn {alive[m['name']]}]"
        print(f"  {m['name']:<24}{withteam:>11,.0f}   (alone {alone:>9,.0f}, buffs +{withteam - alone:>9,.0f}){tag}")
    solo = sorted(((member_damage(u, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules), u['name'])
                   for u in U if u['faction'] != banned), reverse=True)
    print('\nBiggest on their own: ' + ', '.join(f'{n} {d:,.0f}' for d, n in solo[:8]))


if __name__ == '__main__':
    main()
