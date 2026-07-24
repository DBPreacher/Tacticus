#!/usr/bin/env python3
"""
Tacticus Legendary Event Analysis Script
Usage:
    python3 le_analysis.py <conditions_file.yaml> [--csv <path_to_csv>]
"""

import csv, sys, os, json, builtins
from itertools import combinations

try:
    import yaml
    def load_conditions(path):
        with open(path) as f: return yaml.safe_load(f)
except ImportError:
    def load_conditions(path):
        if path.endswith(('.yaml','.yml')):
            sys.exit("PyYAML not installed. Run: pip install pyyaml")
        with open(path) as f: return json.load(f)

def load_characters(csv_path):
    chars = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            chars[row['Name']] = row
    return chars

def qualifies(char, col, val):
    if col == 'Faction': return char.get('Faction','') == val
    if col == 'X_Hits':
        try: x = int(char.get('X_Hits_Restriction','0') or 0)
        except ValueError: return False
        if val.startswith('<='): return x <= int(val[2:])
        if val.startswith('>='): return x >= int(val[2:])
        if val.startswith('<'):  return x <  int(val[1:])
        if val.startswith('>'):  return x >  int(val[1:])
    return char.get(col,'N') == val

def intersect_score(team, battles, chars):
    earned = {}
    for battle, cond in battles.items():
        if all(qualifies(chars[n], cond['col'], cond['val']) for n in team):
            earned[battle] = cond['pts']
    return sum(earned.values()), earned

ABILITY_TANKS = set()  # Future ability-based tanks go here
DAMAGE_REDUCTION = {'Tyrant Guard', 'Thothmek'}  # DR for all; Thothmek best in Mechanical teams

# Named priority picks — characters/pairs the player has specifically invested in.
# PRIORITY_SOLO members count whenever present. PRIORITY_PAIRS only count when
# BOTH members of a pair are in the same team — one without the other earns nothing.
# This is a tiebreaker bonus only (see meta_score) — it never outweighs raw battle
# points, same tier as the existing Damage Reduction / Healer / Tank scoring.
PRIORITY_SOLO = {'Tyrant Guard'}
PRIORITY_PAIRS = [
    {'Nauseous Rotbone', 'Maladus'},
    {'Aleph-Null', "Re'vas"},
    {"Tan Gi'da", 'Actus'},
]

def meta_flags(name, char):
    flags = []
    if name in PRIORITY_SOLO:        flags.append('PRIORITY')
    if char.get('Healer')=='Y':      flags.append('HEALER')
    if char.get('Self_Heal')=='Y':   flags.append('SELF-HEAL')
    if char.get('Mechanic')=='Y':    flags.append('MECHANIC')
    if char.get('Terminator_Armour')=='Y' or char.get('Mk_X_Gravis')=='Y':
        flags.append('TANK(trait)')
    if name in DAMAGE_REDUCTION:     flags.append('DMG-REDUCTION')
    elif name in ABILITY_TANKS:      flags.append('TANK(ability)')
    if char.get('Resilient')=='Y':   flags.append('RESILIENT')
    return flags

def char_line(name, chars, prefix='    '):
    mf = meta_flags(name, chars[name])
    tag = '  [' + ' | '.join(mf) + ']' if mf else ''
    return prefix + name + ' (' + chars[name].get('Faction','') + ')' + tag

def meta_score(team_names, chars):
    """Score a team against the meta target.

    Priority order:
    0. Named priority picks (solo, or pairs where BOTH members are present)
    1. Damage Reduction (Tyrant Guard = any team; Thothmek = Mechanical teams)
    2. Support: Mechanics (2) if Mechanical team, Healers (2) otherwise
    3. Self-Heal (1)
    4. Tanks — Terminator Armour / Mk X Gravis (2)
    5. Resilient — minor bonus

    A team is considered Mechanical if 3+ members have Mechanical=Y.
    Good Mechanical pairings: Re'vas + Aleph-Null, Tan Gi'da + Actus.
    """
    team_set = set(team_names)
    n_priority = (len(team_set & PRIORITY_SOLO) +
                  sum(1 for pair in PRIORITY_PAIRS if pair <= team_set))

    n_h          = sum(1 for n in team_names if chars[n].get('Healer','N')=='Y')
    n_sh         = sum(1 for n in team_names if chars[n].get('Self_Heal','N')=='Y')
    n_t          = sum(1 for n in team_names if (
                       chars[n].get('Terminator_Armour','N')=='Y' or
                       chars[n].get('Mk_X_Gravis','N')=='Y'))
    n_mech_chars = sum(1 for n in team_names if chars[n].get('Mechanical','N')=='Y' or chars[n].get('Living_Metal','N')=='Y')  # Living Metal counts as Mechanical
    n_mechanic   = sum(1 for n in team_names if chars[n].get('Mechanic','N')=='Y')
    n_r          = sum(1 for n in team_names if chars[n].get('Resilient','N')=='Y')

    # Damage Reduction
    n_dr_guard   = sum(1 for n in team_names if n == 'Tyrant Guard')
    n_dr_thotmek = sum(1 for n in team_names if n == 'Thothmek')

    score = 0

    # 0. Named priority picks — highest tier. Solo picks count on their own;
    #    paired picks only count when both members are present in the team.
    score += n_priority * 60

    # 1. Damage Reduction — highest priority
    score += min(n_dr_guard, 1) * 50       # Tyrant Guard: full value any team
    mech_threshold = n_mech_chars >= 2
    score += min(n_dr_thotmek, 1) * (50 if mech_threshold else 25)

    # 2. Support — Mechanics for Mechanical teams, Healers for standard teams
    is_mech_team = n_mech_chars >= 3
    if is_mech_team:
        score += min(n_mechanic, 2) * 30   # Mechanics are the healers here
        score += min(n_h, 1) * 8           # Healers less useful (can't heal Mechanical)
    else:
        score += min(n_h, 2) * 30          # Standard healing
        score += min(n_mechanic, 1) * 8    # Mechanics not primary support

    # 3. Self-Heal — always valuable (Aleph-Null especially in Mechanical teams)
    score += min(n_sh, 1) * 28

    # 4. Tanks (trait-based)
    score += min(n_t, 2) * 20

    # 5. Resilient — minor bonus
    score += min(n_r, 3) * 3

    return score

def best_team_from_pool(pool, battles, chars, size=5):
    """
    Best team of exactly `size` from pool.
    Primary sort: intersection score (pts earned).
    Tiebreaker: meta composition score (2H + 2T + 1SH target).
    Falls back to meta-priority sort for pools > 25.
    """
    if not pool: return [], 0, {}
    actual = min(size, len(pool))
    if len(pool) <= 25:
        best = (0, 0, {}, [])  # (score, meta, earned, team)
        for combo in combinations(pool, actual):
            s, e = intersect_score(list(combo), battles, chars)
            m = meta_score(combo, chars)
            if s > best[0] or (s == best[0] and m > best[1]):
                best = (s, m, e, list(combo))
        return best[3], best[0], best[2]
    else:
        def priority(n):
            c = chars[n]
            # Named priority picks are intentionally NOT weighted here. This fallback
            # (used when a candidate pool exceeds 25 characters) sorts individuals by
            # generic composition value only, with no visibility into which battle
            # conditions the team ends up covering — weighting it toward priority
            # picks pulled in characters that satisfied the target condition but broke
            # bundling with other still-open conditions, costing an extra token in
            # testing. The priority tiebreaker only applies in the exhaustive combo
            # search above (pools <=25), where it's proven not to affect coverage.
            return (int(n in DAMAGE_REDUCTION)*50 +
                    int(c.get('Healer','N')=='Y')*30 +
                    int(c.get('Self_Heal','N')=='Y')*28 +
                    int(c.get('Mechanic','N')=='Y')*25 +
                    int(c.get('Terminator_Armour','N')=='Y' or c.get('Mk_X_Gravis','N')=='Y')*20 +
                    int(n in ABILITY_TANKS)*20 +
                    int(c.get('Resilient','N')=='Y')*3)
        team = sorted(pool, key=priority, reverse=True)[:actual]
        s, e = intersect_score(team, battles, chars)
        return team, s, e

def most_efficient_starting_team(battle_pools, battles, chars):
    """Best team of size 3-5 covering most pts in a single deployment."""
    best = (0, {}, [], 0)
    seen = set()
    for r in range(1, 4):
        for cond_combo in combinations(list(battles.keys()), r):
            pool = sorted(set.intersection(*[set(battle_pools[b]) for b in cond_combo]))
            key = frozenset(pool)
            if key in seen or len(pool) < 3: continue
            seen.add(key)
            for size in [3, 4, 5]:
                if len(pool) < size: continue
                team, score, earned = best_team_from_pool(pool, battles, chars, size)
                if score > best[0]: best = (score, earned, team, size)
    return best

def greedy_coverage(battles, battle_pools, all_eligible, chars):
    """
    Greedy coverage — always produces 5-man teams.
    If the intersection pool for target conditions has < 5 chars,
    falls back to the full eligible pool for the best 5-man available.
    """
    remaining = set(battles.keys())
    teams = []

    while remaining:
        sorted_rem = sorted(remaining, key=lambda b: battles[b]['pts'], reverse=True)
        best_info = None

        for r in range(min(3, len(sorted_rem)-1), -1, -1):
            found = False
            others = sorted_rem[1:] if r > 0 else []
            for other in (list(combinations(others, r)) if r > 0 else [()]):
                conds = [sorted_rem[0]] + list(other)
                intersection = sorted(set.intersection(*[set(battle_pools[b]) for b in conds]))

                if len(intersection) < 3: continue  # too small even for minimum team

                # Use intersection pool if >=5 chars; else fall back to full eligible
                limited = len(intersection) < 5
                search_pool = intersection if not limited else all_eligible

                # Score only against conditions not yet claimed by an earlier team —
                # a team shouldn't get credit (or be penalised) for conditions another
                # team has already banked, since each stage's points are earned once.
                remaining_battles = {b: battles[b] for b in remaining}
                team, score, earned = best_team_from_pool(search_pool, remaining_battles, chars, 5)
                newly = set(earned.keys()) & remaining
                val = sum(battles[b]['pts'] for b in newly)

                if val > 0 and (best_info is None or val > best_info[0]):
                    best_info = (val, score, team, earned, newly, intersection, limited)
                    found = True
            if found: break

        if best_info is None: break
        _, score, team, earned, newly, intersection, limited = best_info
        teams.append((score, {b: battles[b]['pts'] for b in newly}, team, earned, intersection, limited))
        remaining -= newly

    return teams, remaining

def analyse_track(track_name, track_cfg, chars):
    print('\n' + '='*65)
    print('  ' + track_name.upper() + ' TRACK')
    print('='*65)

    battles = {}
    for b in track_cfg['battles']:
        battles[b['name']] = {'col': b['col'], 'val': b['val'], 'pts': b['pts']}

    allowed  = track_cfg.get('allowed_alliances', [])
    excluded = track_cfg.get('excluded_factions', [])
    eligible = {n: c for n, c in chars.items()
                if (not allowed or c.get('Alliance','') in allowed)
                and c.get('Faction','') not in excluded
                and c.get('Is_MoW','N') != 'Y'}
    all_elig = list(eligible.keys())

    total_pts = sum(v['pts'] for v in battles.values())
    print('\n  Available pts: ' + str(total_pts) +
          ' | Eligible characters: ' + str(len(eligible)))

    # Per-battle summary (count only — no character listing)
    battle_pools = {}
    for bname, bcond in battles.items():
        pool = sorted([n for n in eligible if qualifies(eligible[n], bcond['col'], bcond['val'])])
        battle_pools[bname] = pool
        flag = '⚠️ ' if len(pool) < 6 else '✅'
        print('  ' + flag + bname + ' (' + str(bcond['pts']) + 'pts): ' + str(len(pool)) + ' chars')

    # Most efficient starting team
    print('\n  ' + '-'*50)
    print('  MOST EFFICIENT STARTING TEAM')
    print('  ' + '-'*50)
    score, earned, team, sz = most_efficient_starting_team(battle_pools, battles, chars)
    if team:
        cond_str = ' + '.join(sorted(earned.keys(), key=lambda x: earned[x], reverse=True))
        print('  ' + str(sz) + '-man | ' + str(score) + 'pts | Covers: ' + cond_str)
        # Pool for starting team conditions
        start_conds = list(earned.keys())
        start_pool = sorted(set.intersection(*[set(battle_pools[b]) for b in start_conds]))
        print('  Full eligible pool (' + str(len(start_pool)) + '):')
        for n in start_pool: print(char_line(n, chars))
        print('  Recommended:')
        for n in team:   print(char_line(n, chars, '    * '))
    else:
        print('  Could not find a valid starting team.')

    # Full coverage teams
    print('\n  ' + '-'*50)
    print('  FULL COVERAGE TEAMS (5-man)')
    print('  ' + '-'*50)
    teams, uncovered = greedy_coverage(battles, battle_pools, all_elig, chars)
    total_cycle = sum(s for s,_,_,_,_,_ in teams)
    print('  Tokens: ' + str(len(teams)) + ' | Total pts/cycle: ' + str(total_cycle))
    if uncovered:
        print('  ⚠️  Conditions not covered: ' + ', '.join(uncovered))

    usage = {}
    for _,_,combo,_,_,_ in teams:
        for n in combo: usage[n] = usage.get(n,0) + 1
    high_priority = {n for n,c in usage.items() if c > 1}

    print()
    for tidx, (sc, newly_dict, combo, full_earned, intersection, limited) in enumerate(teams, 1):
        conds = ' + '.join(sorted(newly_dict.keys(), key=lambda x: newly_dict[x], reverse=True))
        full_pts = sum(full_earned.values())

        print('  TEAM ' + str(tidx) + ' | Newly covers: ' + conds +
              ' | Pts/deployment: ' + str(full_pts))

        if limited:
            print('  ⚠️  Pure intersection pool only ' + str(len(intersection)) +
                  ' chars (< 5) — team sourced from wider eligible pool')
            print('  Pure intersection pool (' + str(len(intersection)) + '):')
            for n in intersection: print(char_line(n, chars, '    '))
        else:
            print('  Full eligible pool (' + str(len(intersection)) + '):')
            for n in intersection: print(char_line(n, chars, '    '))

        print('  Recommended 5:')
        for n in combo: print(char_line(n, chars, '    * '))
        shared = [n for n in combo if n in high_priority]
        if shared:
            print('  ★ High-priority investment (multi-team): ' + ', '.join(shared))
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 le_analysis.py <conditions.yaml> [--csv <path>]")
        sys.exit(1)

    conditions_path = sys.argv[1]
    csv_path = 'tacticus_characters.csv'
    if '--csv' in sys.argv:
        csv_path = sys.argv[sys.argv.index('--csv') + 1]

    if not os.path.exists(conditions_path): sys.exit('Not found: ' + conditions_path)
    if not os.path.exists(csv_path):        sys.exit('Not found: ' + csv_path)

    config = load_conditions(conditions_path)
    chars  = load_characters(csv_path)

    le_name   = config.get('le_name', 'Unknown')
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in le_name)
    out_path  = safe_name + '_analysis.txt'

    lines = []
    orig_print = builtins.print
    def cap(*args, **kwargs):
        line = ' '.join(str(a) for a in args)
        orig_print(line)
        lines.append(line)
    builtins.print = cap

    print('\n' + '█'*65)
    print('  LE ANALYSIS: ' + le_name)
    print('█'*65)
    print('  Characters loaded: ' + str(len(chars)))
    print('  NOTE: Defeat all enemies objectives ignored (base rewards).')

    for track in config.get('tracks', []):
        analyse_track(track['name'], track, chars)

    print('\n' + '='*65)
    print('  ANALYSIS COMPLETE')
    print('='*65 + '\n')

    builtins.print = orig_print

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('>>> Saved to: ' + out_path)

if __name__ == '__main__':
    main()