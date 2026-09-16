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


def member_damage(member, mates, boss, ds, rows, sp, lv, trig, act, gear):
    """one character's damage over the 6 turns: the active turn plus normal attacks"""
    toks = buffs_for(member, mates, rows, lv, trig, act, 'Immune' in boss['traits'])
    spec = sp['active'].get(member['name']) if act else None
    a, spec2, _ = sm.buffed(member, toks, spec, gear) if toks else (member, spec, 0.0)
    normal = bm.best_attack(a, boss, trig, ds, False, False)[0]
    if spec2:
        first = sum(x[0] for x in bm.opener(a, boss, trig, spec2, ds))
        return max(first, normal) + normal * (TURNS - 1)
    return normal * TURNS


def team_damage(team, boss, ds, rows, sp, lv, trig, act, gear):
    return sum(member_damage(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp, lv, trig, act, gear)
               for m in team)


def best_team(U, boss, ds, rows, sp, lv, trig, act, gear, banned, passes=3):
    """greedy five, then swap each slot for anything better until it stops improving"""
    pool = [u for u in U if u['faction'] != banned]
    names = lambda team: {u['name'] for u in team}
    team = []
    for _ in range(TEAM):
        team.append(max((u for u in pool if u['name'] not in names(team)),
                        key=lambda u: team_damage(team + [u], boss, ds, rows, sp, lv, trig, act, gear)))
    score = team_damage(team, boss, ds, rows, sp, lv, trig, act, gear)
    for _ in range(passes):
        improved = False
        for i in range(TEAM):
            for u in pool:
                if u['name'] in names(team):
                    continue
                trial = team[:i] + [u] + team[i + 1:]
                s = team_damage(trial, boss, ds, rows, sp, lv, trig, act, gear)
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
    args = ap.parse_args()
    g = game()
    fs = [f for f in fights(g) if f['name'].lower().startswith(args.boss.lower())]
    fight = next((f for f in fs if f['level'] == args.level), fs[-1])
    boss, ds, dbf = boss_defender(g, fight, args.debuffs)
    act = not args.no_active
    U, sp = setting(args.tier, args.ability, args.trig, act, args.gear)
    rows = sm.load_rows('Attack')
    banned = FACTION_ID.get(fight['faction'], fight['faction'])
    print(f"{fight['name']} L{fight['level']} ({fight['rarity']}, tier {fight['tier']}): {fight['hp']:,} health, "
          f"{boss['arm']:,.0f} Armour, blocks {ds['bc'] * 100:.0f}% for {ds['bd']:,.0f}"
          + (f" · side battles cleared: -{dbf['armour']:.0f}% Armour, -{dbf['block']:.0f}% block" if args.debuffs else ''))
    print(f"no {banned} allowed · {TURNS} turns · {args.tier} abilities {args.ability} "
          f"{'standard gear' if args.gear else 'no gear'} {'all triggered' if args.trig else 'always-on'} "
          f"active {'on' if act else 'off'}")
    team, score = best_team(U, boss, ds, rows, sp, args.ability, args.trig, act, args.gear, banned)
    print(f"\nBest five: {score:,.0f} damage in {TURNS} turns ({score / fight['hp'] * 100:.2f}% of the boss)")
    for m in team:
        alone = member_damage(m, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear)
        withteam = member_damage(m, [x for x in team if x['name'] != m['name']], boss, ds, rows, sp, args.ability, args.trig, act, args.gear)
        print(f"  {m['name']:<24}{withteam:>11,.0f}   (alone {alone:>9,.0f}, buffs +{withteam - alone:>9,.0f})")
    solo = sorted(((member_damage(u, [], boss, ds, rows, sp, args.ability, args.trig, act, args.gear), u['name'])
                   for u in U if u['faction'] != banned), reverse=True)
    print('\nBiggest on their own: ' + ', '.join(f'{n} {d:,.0f}' for d, n in solo[:8]))


if __name__ == '__main__':
    main()
