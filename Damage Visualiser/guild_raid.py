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
import argparse, csv, json, os
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
    """what winning both side battles takes off this boss (each chain in full)"""
    tot = dict(armour=0.0, block=0.0, steps=0)
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


def boss_rules(g, fight):
    """the boss passives that change how much damage it takes, read from the game data at its ability level.
    Everything else about a boss (its own attacks, summons, what you can dodge) isn't modelled yet."""
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
            out['notes'].append(f"only the first {out['diminish'][0]} hit(s) of an attack land in full, "
                                f"each one after that {out['diminish'][1]:.0f}% weaker than the last")
        elif k == 'NoctilithBeacons':                   # Szarekh: Psykers do less
            out['psyker_pct'] = const(k, 'dmgPctReduction', 0)
            out['notes'].append(f"Psykers deal -{out['psyker_pct']:.0f}% damage")
        elif k == 'TheEmperorsShield':                  # Lion: melee hits give him block for the turn
            out['block_ramp'] = const(k, 'blockChance', 0)
            out['notes'].append(f"every melee hit gives +{out['block_ramp']:.0f}% block chance for the turn, "
                                "and he hits back at attacks he blocks twice")
        elif k == 'ObeisanceGenerators':                # Szarekh: don't charge him
            out['charge_hits'] = int(const(k, 'hitsReduction', 0))
            out['notes'].append(f"charging costs {out['charge_hits']} hits (so stand still and attack)")
    return out


def hits_of(a, w):
    """how many hits an attack scores, for the boss rules that count hits"""
    n = w['hits']
    for e in (a.get('ps') or ([], []))[0]:
        if e['kind'] == 'hits' and e['scope'] in ('all', w['kind']):
            n += e['value']
        if e['kind'] == 'extra' and e['scope'] in ('all', w['kind']):
            n += e['part']['hits']
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
    U, sp, _, _ = sm.setting_units(units, specs, lv, trig, act, gear)
    return U, sp


def buffs_for(member, mates, rows, lv, trig, act, immune):
    """the Attack-side tokens this member picks up from its team-mates. Each buff goes to the team-mates
    it helps most (biggest Damage first), as far as its reach allows."""
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
            for t in sm.tokens_for(r, member, ab, relic, lv, trig):
                if immune and t['kind'] == 'armour':          # a Boss's Armour can't be reduced
                    continue
                toks.append(t)
    return toks


def member_damage(member, mates, boss, ds, rows, sp, lv, trig, act, gear, rules=None, extra=None):
    """one character's damage over the 6 turns: the active turn plus normal attacks.
    extra: flat Damage added to this character's stat (Laviscus's Outrage, the Neurothrope's parasite)."""
    rules = rules or dict(diminish=None, psyker_pct=0.0, block_ramp=0.0, charge_hits=0, notes=[])
    toks = buffs_for(member, mates, rows, lv, trig, act, 'Immune' in boss['traits'])
    spec = sp['active'].get(member['name']) if act else None
    a, spec2, _ = sm.buffed(member, toks, spec, gear) if toks else (member, spec, 0.0)
    if extra:
        a = dict(a, dmg=a['dmg'] + extra)
    dmg, _, w = bm.best_attack(a, boss, trig, ds, False, False)
    f = rule_factor(a, w, rules, member)
    normal = dmg * f
    if spec2:
        first = sum(x[0] for x in bm.opener(a, boss, trig, spec2, ds)) * f
        return max(first, normal) + normal * (TURNS - 1)
    return normal * TURNS


def biggest_hit(member, mates, boss, ds, rows, sp, lv, trig, act, gear):
    """this character's biggest single hit on the boss (what Laviscus's Outrage feeds on)"""
    toks = buffs_for(member, mates, rows, lv, trig, act, 'Immune' in boss['traits'])
    a, _, _ = sm.buffed(member, toks, None, gear) if toks else (member, None, 0.0)
    best = 0.0
    for w in a['weapons']:
        if w['type'] in ('Psychic',):              # Outrage only counts non-Psychic hits
            continue
        tot = bm.best_attack(a, boss, trig, ds, False, False, w['kind'])[0]
        best = max(best, tot / max(hits_of(a, w), 1))
    return best


def outrage(member, team, boss, ds, rows, sp, lv, trig, act, gear):
    """Laviscus, at face value: every friendly character attacking the boss next to him adds its biggest
    non-Psychic hit to his Outrage, and his Damage goes up by 120% of it. It resets when he attacks, so
    this is what he has each turn."""
    mates = [x for x in team if x['name'] != member['name']]
    pct = sm.value(member['passive'], 'extraDmgPct', lv) / 100
    return pct * sum(biggest_hit(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp, lv, trig, act, gear)
                     for m in mates)


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


def team_damage(team, boss, ds, rows, sp, lv, trig, act, gear, rules=None, tier_key='d3'):
    total = 0.0
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra = 0.0
        if m['name'] == 'Laviscus':
            extra += outrage(m, team, boss, ds, rows, sp, lv, trig, act, gear)
        extra += parasite(m, team, boss, lv, gear, tier_key)
        total += member_damage(m, mates, boss, ds, rows, sp, lv, trig, act, gear, rules, extra)
    return total


def best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, rules=None, anchors=(), passes=3):
    """greedy five, then swap each slot for anything better until it stops improving.
    anchors: characters that must be in the team (the team styles the owner plays)."""
    pool = [u for u in U if u['faction'] != banned]
    names = lambda team: {u['name'] for u in team}
    score_of = lambda team: team_damage(team, boss, ds, rows, sp, lv, trig, act, gear, rules)
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
    args = ap.parse_args()
    g = game()
    fs = [f for f in fights(g) if f['name'].lower().startswith(args.boss.lower())]
    fight = next((f for f in fs if f['level'] == args.level), fs[-1])
    boss, ds, dbf = boss_defender(g, fight, args.debuffs)
    rules = boss_rules(g, fight)
    act = not args.no_active
    U, sp = setting(args.tier, args.ability, args.trig, act, args.gear)
    rows = sm.load_rows('Attack')
    banned = FACTION_ID.get(fight['faction'], fight['faction'])
    print(f"{fight['name']} L{fight['level']} ({fight['rarity']}, tier {fight['tier']}): {fight['hp']:,} health, "
          f"{boss['arm']:,.0f} Armour, blocks {ds['bc'] * 100:.0f}% for {ds['bd']:,.0f}"
          + (f" · side battles cleared: -{dbf['armour']:.0f}% Armour, -{dbf['block']:.0f}% block" if args.debuffs else ''))
    for n in rules['notes']:
        print(f'   rule: {n}')
    print(f"no {banned} allowed · {TURNS} turns · {args.tier} abilities {args.ability} "
          f"{'standard gear' if args.gear else 'no gear'} {'all triggered' if args.trig else 'always-on'} "
          f"active {'on' if act else 'off'}")
    if args.team:
        want = [x.strip().lower() for x in args.team.split(',')]
        team = [u for u in U if u['name'].lower() in want]
        score = team_damage(team, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules)
    else:
        team, score = best_team(U, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, banned, rules, tuple(args.anchor))
    print(f"\nBest five: {score:,.0f} damage in {TURNS} turns ({score / fight['hp'] * 100:.2f}% of the boss)")
    for m in team:
        mates = [x for x in team if x['name'] != m['name']]
        extra = (outrage(m, team, boss, ds, rows, sp, args.ability, args.trig, act, args.gear) if m['name'] == 'Laviscus' else 0.0)
        extra += parasite(m, team, boss, args.ability, args.gear, args.tier)
        alone = member_damage(m, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules)
        withteam = member_damage(m, mates, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules, extra)
        tag = f'  (+{extra:,.0f} Damage from the team)' if extra else ''
        print(f"  {m['name']:<24}{withteam:>11,.0f}   (alone {alone:>9,.0f}, buffs +{withteam - alone:>9,.0f}){tag}")
    solo = sorted(((member_damage(u, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear, rules), u['name'])
                   for u in U if u['faction'] != banned), reverse=True)
    print('\nBiggest on their own: ' + ', '.join(f'{n} {d:,.0f}' for d, n in solo[:8]))


if __name__ == '__main__':
    main()
