#!/usr/bin/env python3
"""
Tacticus Legendary Event Analysis Script
=========================================
Usage:
    python3 le_analysis.py <conditions_file.yaml>

The conditions file defines the LE name, track restrictions and battle
conditions. See conditions_template.yaml for format.

Reads character data from tacticus_characters.csv in the same directory,
or from a URL if --csv flag is provided.

Output: full pool listings, most efficient starting team, coverage teams,
meta flags, and high-priority investment characters.
"""

import csv
import sys
import os
import json
from itertools import combinations

# ── Optional YAML support (falls back to JSON if PyYAML not installed) ────────
try:
    import yaml
    def load_conditions(path):
        with open(path) as f:
            return yaml.safe_load(f)
except ImportError:
    def load_conditions(path):
        if path.endswith('.yaml') or path.endswith('.yml'):
            sys.exit("PyYAML not installed. Use a .json conditions file or: pip install pyyaml")
        with open(path) as f:
            return json.load(f)

# ── CSV loading ───────────────────────────────────────────────────────────────
def load_characters(csv_path):
    chars = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            chars[row['Name']] = row
    return chars

# ── Condition evaluation ──────────────────────────────────────────────────────
def qualifies(char, col, val):
    """Check if a character satisfies a single condition."""
    if col == 'Faction':
        return char.get('Faction','') == val
    if col == 'X_Hits':
        try:
            x = int(char.get('X_Hits_Restriction','0') or 0)
        except ValueError:
            return False
        if val.startswith('<='): return x <= int(val[2:])
        if val.startswith('>='): return x >= int(val[2:])
        if val.startswith('<'):  return x <  int(val[1:])
        if val.startswith('>'):  return x >  int(val[1:])
    return char.get(col,'N') == val

def intersect_score(team, battles, chars):
    """Return total pts and earned dict for conditions ALL team members satisfy."""
    earned = {}
    for battle, cond in battles.items():
        col, val, pts = cond['col'], cond['val'], cond['pts']
        if all(qualifies(chars[n], col, val) for n in team):
            earned[battle] = pts
    return sum(earned.values()), earned

# ── Meta flags ────────────────────────────────────────────────────────────────
ABILITY_TANKS = {'Tyrant Guard', 'Thothmek'}

def meta_flags(name, char):
    flags = []
    if char.get('Healer')      == 'Y': flags.append('HEALER')
    if char.get('Self_Heal')   == 'Y': flags.append('SELF-HEAL')
    if char.get('Mechanic')    == 'Y': flags.append('MECHANIC')
    if char.get('Terminator_Armour') == 'Y' or char.get('Mk_X_Gravis') == 'Y':
        flags.append('TANK(trait)')
    if name in ABILITY_TANKS:          flags.append('TANK(ability)')
    if char.get('Resilient')   == 'Y': flags.append('RESILIENT')
    return flags

def char_line(name, chars, prefix='    '):
    mf = meta_flags(name, chars[name])
    tag = '  [' + ' | '.join(mf) + ']' if mf else ''
    return prefix + name + ' (' + chars[name].get('Faction','') + ')' + tag

# ── Team finding ──────────────────────────────────────────────────────────────
def best_team_from_pool(pool, battles, chars, size=5):
    """
    Find the best team of `size` from pool.
    Fast exhaustive search if pool ≤ 25; meta-priority sort otherwise.
    """
    if not pool:
        return [], 0, {}
    actual = min(size, len(pool))
    if len(pool) <= 25:
        best = (0, {}, [])
        for combo in combinations(pool, actual):
            s, e = intersect_score(list(combo), battles, chars)
            if s > best[0]:
                best = (s, e, list(combo))
        return best[2], best[0], best[1]
    else:
        def priority(n):
            c = chars[n]
            return (
                int(c.get('Healer','N')=='Y') * 3 +
                int(c.get('Self_Heal','N')=='Y') * 3 +
                int(c.get('Terminator_Armour','N')=='Y' or c.get('Mk_X_Gravis','N')=='Y') * 2 +
                int(n in ABILITY_TANKS) * 2 +
                int(c.get('Resilient','N')=='Y')
            )
        team = sorted(pool, key=priority, reverse=True)[:actual]
        s, e = intersect_score(team, battles, chars)
        return team, s, e

def most_efficient_starting_team(battle_pools, battles, chars):
    """
    Evaluate all intersections of 1-3 conditions for team sizes 3-5.
    Return the combo with highest intersection score per token (= per deployment).
    """
    best = (0, {}, [], 0)
    seen = set()
    battle_names = list(battles.keys())
    for r in range(1, 4):
        for cond_combo in combinations(battle_names, r):
            pool_sets = [set(battle_pools[b]) for b in cond_combo]
            pool = sorted(set.intersection(*pool_sets))
            key = frozenset(pool)
            if key in seen or len(pool) < 3:
                continue
            seen.add(key)
            for size in [3, 4, 5]:
                if len(pool) < size:
                    continue
                team, score, earned = best_team_from_pool(pool, battles, chars, size)
                if score > best[0]:
                    best = (score, earned, team, size)
    return best

def greedy_coverage(battles, battle_pools, chars):
    """
    Greedy team builder: always pick the team that covers the most
    uncovered point value in a single deployment.
    """
    remaining = set(battles.keys())
    teams = []

    while remaining:
        sorted_rem = sorted(remaining, key=lambda b: battles[b]['pts'], reverse=True)
        best_info = None

        for r in range(min(3, len(sorted_rem)-1), -1, -1):
            found = False
            others_pool = sorted_rem[1:] if r > 0 else []
            others_combos = list(combinations(others_pool, r)) if r > 0 else [()]
            for other in others_combos:
                conds = [sorted_rem[0]] + list(other)
                pool_sets = [set(battle_pools[b]) for b in conds]
                pool = sorted(set.intersection(*pool_sets))
                if len(pool) < 3:
                    continue
                team, score, earned = best_team_from_pool(pool, battles, chars)
                newly = set(earned.keys()) & remaining
                val = sum(battles[b]['pts'] for b in newly)
                if val > 0 and (best_info is None or val > best_info[0]):
                    best_info = (val, score, team, earned, newly)
                    found = True
            if found:
                break

        if best_info is None:
            break
        _, score, team, earned, newly = best_info
        teams.append((score, {b: battles[b]['pts'] for b in newly}, team, earned))
        remaining -= newly

    return teams, remaining

# ── Track analysis ────────────────────────────────────────────────────────────
def analyse_track(track_name, track_cfg, chars):
    print('\n' + '=' * 65)
    print('  ' + track_name.upper() + ' TRACK')
    print('=' * 65)

    # Build battle dict
    battles = {}
    for b in track_cfg['battles']:
        battles[b['name']] = {'col': b['col'], 'val': b['val'], 'pts': b['pts']}

    # Filter eligible characters
    allowed_alliances = track_cfg.get('allowed_alliances', [])
    excluded_factions = track_cfg.get('excluded_factions', [])
    eligible = {
        n: c for n, c in chars.items()
        if (not allowed_alliances or c.get('Alliance','') in allowed_alliances)
        and c.get('Faction','') not in excluded_factions
        and c.get('Is_MoW','N') != 'Y'
    }

    total_pts = sum(v['pts'] for v in battles.values())
    print('\n  Available pts: ' + str(total_pts) +
          ' | Eligible characters: ' + str(len(eligible)))

    # Per-battle pools
    battle_pools = {}
    for bname, bcond in battles.items():
        pool = sorted([n for n in eligible
                       if qualifies(eligible[n], bcond['col'], bcond['val'])])
        battle_pools[bname] = pool
        flag = '⚠️ ' if len(pool) < 6 else '✅'
        print('\n  ' + flag + bname + ' (' + str(bcond['pts']) + 'pts): ' +
              str(len(pool)) + ' chars')
        for n in pool:
            print(char_line(n, chars))

    # Most efficient starting team
    print('\n  ' + '-'*50)
    print('  MOST EFFICIENT STARTING TEAM')
    print('  ' + '-'*50)
    score, earned, team, sz = most_efficient_starting_team(battle_pools, battles, chars)
    if team:
        cond_str = ' + '.join(sorted(earned.keys(), key=lambda x: earned[x], reverse=True))
        print('  ' + str(sz) + '-man | ' + str(score) + 'pts | Covers: ' + cond_str)
        for n in team:
            print(char_line(n, chars))
    else:
        print('  Could not find a valid starting team.')

    # Full coverage
    print('\n  ' + '-'*50)
    print('  FULL COVERAGE TEAMS')
    print('  ' + '-'*50)
    teams, uncovered = greedy_coverage(battles, battle_pools, chars)
    total_cycle = sum(s for s,_,_,_ in teams)
    print('  Tokens: ' + str(len(teams)) +
          ' | Total pts/cycle: ' + str(total_cycle))
    if uncovered:
        print('  ⚠️  Conditions not covered: ' + ', '.join(uncovered))

    # Identify high-priority (appears in 2+ teams)
    usage = {}
    for _,_,combo,_ in teams:
        for n in combo:
            usage[n] = usage.get(n, 0) + 1
    high_priority = {n for n, c in usage.items() if c > 1}

    print()
    for tidx, (sc, newly_dict, combo, full_earned) in enumerate(teams, 1):
        conds = ' + '.join(sorted(newly_dict.keys(), key=lambda x: newly_dict[x], reverse=True))
        full_pts = sum(full_earned.values())
        pool_sets = [set(battle_pools[b]) for b in full_earned.keys()]
        full_pool = sorted(set.intersection(*pool_sets)) if pool_sets else []

        print('  TEAM ' + str(tidx) + ' | Newly covers: ' + conds +
              ' | Pts/deployment: ' + str(full_pts))
        print('  Full eligible pool (' + str(len(full_pool)) + '):')
        for n in full_pool:
            print(char_line(n, chars, '    '))
        print('  Recommended:')
        for n in combo:
            print(char_line(n, chars, '    * '))
        shared = [n for n in combo if n in high_priority]
        if shared:
            print('  ★ High-priority investment (multi-team): ' + ', '.join(shared))
        print()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 le_analysis.py <conditions_file.yaml|json>")
        print("       python3 le_analysis.py <conditions_file.yaml|json> --csv <path_to_csv>")
        sys.exit(1)

    conditions_path = sys.argv[1]

    # Optional CSV path override
    csv_path = 'tacticus_characters.csv'
    if '--csv' in sys.argv:
        idx = sys.argv.index('--csv')
        csv_path = sys.argv[idx + 1]

    if not os.path.exists(conditions_path):
        sys.exit('Conditions file not found: ' + conditions_path)
    if not os.path.exists(csv_path):
        sys.exit('CSV not found: ' + csv_path +
                 '\nRun from the repo data/ directory or use --csv <path>')

    config   = load_conditions(conditions_path)
    chars    = load_characters(csv_path)

    print('\n' + '█'*65)
    print('  LE ANALYSIS: ' + config.get('le_name', 'Unknown'))
    print('█'*65)
    print('  Characters loaded: ' + str(len(chars)))
    print('  NOTE: Defeat all enemies objectives are ignored (base rewards).')

    for track in config.get('tracks', []):
        analyse_track(track['name'], track, chars)

    print('\n' + '='*65)
    print('  ANALYSIS COMPLETE')
    print('='*65 + '\n')

if __name__ == '__main__':
    main()
