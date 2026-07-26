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
    if char.get('Parrying')=='Y':    flags.append('PARRYING')
    if char.get('Shielding')=='Y':   flags.append('SHIELDING')
    if char.get('Spawner')=='Y':     flags.append('SPAWNER')
    return flags

def char_line(name, chars, prefix='    '):
    mf = meta_flags(name, chars[name])
    tag = '  [' + ' | '.join(mf) + ']' if mf else ''
    return prefix + name + ' (' + chars[name].get('Faction','') + ')' + tag

REUSE_BONUS = 15  # per-character tiebreak bonus for reusing an already-invested pick

def meta_score(team_names, chars, usage=None):
    """Score a team against the meta target.

    Priority order:
    0. Named priority picks (solo, or pairs where BOTH members are present)
    1. Damage Reduction (Tyrant Guard = any team; Thothmek = Mechanical teams)
    2. Support: Mechanics (2) if Mechanical team, Healers (2) otherwise
    3. Self-Heal (1)
    4. Tanks — Terminator Armour / Mk X Gravis (2)
    5. Resilient — minor bonus
    6. Reuse — already-invested-in-this-track tiebreak (see REUSE_BONUS)
    7. Parrying / Shielding / Spawner — last-resort differentiators, weighted
       below everything else above (including Resilient). No preference
       between the three — they're equally weak tiebreaks used only to
       separate otherwise-identical candidates.

    A team is considered Mechanical if 3+ members have Mechanical=Y.
    Good Mechanical pairings: Re'vas + Aleph-Null, Tan Gi'da + Actus.

    `usage` (optional): {name: count} of characters already placed on
    earlier teams within the same track. This is a TIEBREAKER ONLY — it
    never outweighs raw battle points (score `s` in best_team_from_pool),
    same tier as the existing named-priority/DR/Healer/Tank bonuses. It
    exists so that, among equally-scoring teams, we prefer reusing a
    character already committed to elsewhere in the track over spreading
    investment across an extra unique roster slot.
    """
    usage = usage or {}
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
    n_parry      = sum(1 for n in team_names if chars[n].get('Parrying','N')=='Y')
    n_shield     = sum(1 for n in team_names if chars[n].get('Shielding','N')=='Y')
    n_spawn      = sum(1 for n in team_names if chars[n].get('Spawner','N')=='Y')

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

    # 6. Reuse — prefer characters already committed to this track over new picks
    n_reused = sum(1 for n in team_names if usage.get(n, 0) > 0)
    score += n_reused * REUSE_BONUS

    # 7. Last-resort differentiators — weighted below Resilient (weight 1 each,
    #    no cap, no preference between them). Only ever matters once every
    #    stronger tier above is fully tied.
    score += n_parry * 1
    score += n_shield * 1
    score += n_spawn * 1

    return score

def best_team_from_pool(pool, battles, chars, size=5, usage=None):
    """
    Best team of exactly `size` from pool.
    Primary sort: intersection score (pts earned).
    Tiebreaker: meta composition score (2H + 2T + 1SH target, plus reuse — see meta_score).

    For pools > 25, a full exhaustive combo search is too expensive, so we
    pre-filter to a shortlist first. That shortlist ALWAYS force-includes
    any PRIORITY_SOLO member and both halves of any PRIORITY_PAIRS pair
    present in the pool — a per-character priority score can't express "this
    character is only worth a lot if a specific partner is also picked", so
    without forcing them in, a pairing like Aleph-Null + Re'vas could lose
    to a stronger-looking individual (e.g. a Mechanic with a reuse bonus)
    even though the pair together would have scored much higher as a team.
    The shortlist is then run through the same exhaustive scorer as the
    <=25 case, so pairing/meta bonuses are evaluated correctly either way.
    """
    if not pool: return [], 0, {}
    actual = min(size, len(pool))
    if len(pool) > 25:
        usage = usage or {}
        pool_set = set(pool)
        forced = set(PRIORITY_SOLO) & pool_set
        for pair in PRIORITY_PAIRS:
            if pair <= pool_set:
                forced |= pair

        def priority(n):
            c = chars[n]
            # Named priority PAIRS are intentionally not weighted here (a
            # per-character score can't express joint-only value) — they're
            # guaranteed a seat via `forced` above instead. DR/solo picks
            # still get weighted below since they're valuable individually
            # too, not just as part of a pair.
            return (int(n in DAMAGE_REDUCTION)*50 +
                    int(c.get('Healer','N')=='Y')*30 +
                    int(c.get('Self_Heal','N')=='Y')*28 +
                    int(c.get('Mechanic','N')=='Y')*25 +
                    int(c.get('Terminator_Armour','N')=='Y' or c.get('Mk_X_Gravis','N')=='Y')*20 +
                    int(n in ABILITY_TANKS)*20 +
                    int(c.get('Resilient','N')=='Y')*3 +
                    int(usage.get(n, 0) > 0)*REUSE_BONUS +
                    int(c.get('Parrying','N')=='Y')*1 +
                    int(c.get('Shielding','N')=='Y')*1 +
                    int(c.get('Spawner','N')=='Y')*1)

        ranked = sorted(pool_set - forced, key=priority, reverse=True)
        shortlist = list(forced) + ranked
        pool = shortlist[:25] if len(shortlist) > 25 else shortlist

    best = (0, 0, {}, [])  # (score, meta, earned, team)
    for combo in combinations(pool, actual):
        s, e = intersect_score(list(combo), battles, chars)
        m = meta_score(combo, chars, usage)
        if s > best[0] or (s == best[0] and m > best[1]):
            best = (s, m, e, list(combo))
    return best[3], best[0], best[2]

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

def enumerate_achievable_bundles(battles, battle_pools):
    """
    Every non-empty subset of a track's objectives where at least 5 characters
    individually satisfy ALL objectives in that subset simultaneously — i.e. a
    real, undiluted 5-man team could exist for it. No fallback pool, no filler:
    if fewer than 5 characters qualify for a combination, that combination is
    simply not achievable by any team, full stop.
    """
    names = list(battles.keys())
    n = len(names)
    bundles = []
    for mask in range(1, 1 << n):
        E = frozenset(names[i] for i in range(n) if mask & (1 << i))
        pool = sorted(set.intersection(*[set(battle_pools[c]) for c in E]))
        if len(pool) >= 5:
            bundles.append({'earned': E, 'score': sum(battles[c]['pts'] for c in E), 'pool': pool})
    return bundles

def solve_optimal_coverage(bundles, battles):
    """
    Exact search (not greedy/anchored) over which achievable bundles to combine
    across a track, maximizing total points earned — with fewest tokens only as
    a tiebreak between equal-point options, never trading points for tokens.

    With at most 5 objectives per track this is a tiny state space (<=32), so
    we solve it exactly via memoized recursion rather than approximating.
    """
    memo = {}
    def rec(state):
        if state in memo: return memo[state]
        best = (0, 0, [])  # (points, tokens, [bundle indices])
        for idx, b in enumerate(bundles):
            newly = b['earned'] - state
            if not newly: continue  # would earn nothing new — never worth a token
            gain = sum(battles[c]['pts'] for c in newly)
            sub_pts, sub_tok, sub_path = rec(state | b['earned'])
            cand = (gain + sub_pts, 1 + sub_tok, [idx] + sub_path)
            if cand[0] > best[0] or (cand[0] == best[0] and cand[1] < best[1]):
                best = cand
        memo[state] = best
        return best
    return rec(frozenset())

def optimal_coverage(battles, battle_pools, chars, usage, char_tracks, track_name):
    """
    Finds the true point-maximizing set of 5-man teams for a track (ties broken
    by fewest tokens), then presents them in descending point order, applying
    the reuse tiebreak (REUSE_BONUS) sequentially so later teams prefer
    characters already committed earlier.

    `usage` and `char_tracks` are shared, mutated-in-place dicts passed in from
    main() so that reuse credit — and the resulting notes — carry ACROSS
    tracks, not just within one. `usage`: name -> total times used so far
    (any track). `char_tracks`: name -> set of track names they've appeared in
    so far. Each team's reuse is split into two flavors for reporting:
      - within-track reuse (already on an earlier team in *this* track)
      - cross-track reuse (already committed in a *different* track entirely)
    Cross-track reuse is the bigger win — it means one less character to level
    for the whole event, not just this track — so it's flagged distinctly.
    """
    all_conditions = set(battles.keys())
    bundles = enumerate_achievable_bundles(battles, battle_pools)
    _, _, path = solve_optimal_coverage(bundles, battles)
    chosen = [bundles[i] for i in path]
    chosen.sort(key=lambda b: b['score'], reverse=True)

    claimed = set()
    teams = []
    for b in chosen:
        remaining_conds = all_conditions - claimed
        if not remaining_conds: break
        remaining_battles = {c: battles[c] for c in remaining_conds}
        team, score, earned = best_team_from_pool(b['pool'], remaining_battles, chars, 5, usage)
        newly = set(earned.keys()) & remaining_conds
        if not newly: continue  # fully subsumed by higher-priority teams already listed

        within_reused = sorted(n for n in team if usage.get(n, 0) > 0 and track_name in char_tracks.get(n, set()))
        cross_reused_tracks = {n: sorted(char_tracks.get(n, set()))
                                for n in team
                                if usage.get(n, 0) > 0 and track_name not in char_tracks.get(n, set())}

        teams.append((score, {c: battles[c]['pts'] for c in newly}, team, earned, b['pool'],
                      within_reused, cross_reused_tracks))
        claimed |= newly
        for n in team:
            usage[n] = usage.get(n, 0) + 1
            char_tracks.setdefault(n, set()).add(track_name)

    return teams, all_conditions - claimed

def analyse_track(track_name, track_cfg, chars, global_usage, global_char_tracks):
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

    total_pts = sum(v['pts'] for v in battles.values())
    print('\n  Available pts: ' + str(total_pts) +
          ' | Eligible characters: ' + str(len(eligible)))
    print('  Enemies: ' + track_cfg.get('enemies', 'Unknown'))
    print('  Eligible factions: ' + (' & '.join(allowed) if allowed else 'Any'))

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
    teams, uncovered = optimal_coverage(battles, battle_pools, chars, global_usage, global_char_tracks, track_name)
    total_cycle = sum(s for s,_,_,_,_,_,_ in teams)
    print('  Tokens: ' + str(len(teams)) + ' | Total pts/cycle: ' + str(total_cycle))
    if uncovered:
        print('  ⚠️  Conditions not covered by any achievable 5-man team: ' + ', '.join(uncovered))

    track_usage = {}
    for _,_,combo,_,_,_,_ in teams:
        for n in combo: track_usage[n] = track_usage.get(n,0) + 1
    high_priority = {n for n,c in track_usage.items() if c > 1}

    print()
    for tidx, (sc, newly_dict, combo, full_earned, pool, within_reused, cross_reused_tracks) in enumerate(teams, 1):
        conds = ' + '.join(sorted(newly_dict.keys(), key=lambda x: newly_dict[x], reverse=True))
        full_pts = sum(full_earned.values())

        print('  TEAM ' + str(tidx) + ' | Newly covers: ' + conds +
              ' | Pts/deployment: ' + str(full_pts))

        print('  Full eligible pool (' + str(len(pool)) + '):')
        for n in pool: print(char_line(n, chars, '    '))

        print('  Recommended 5:')
        for n in combo: print(char_line(n, chars, '    * '))
        shared = [n for n in combo if n in high_priority]
        if shared:
            print('  ★ High-priority investment (multi-team): ' + ', '.join(shared))
        if within_reused:
            saved = len(within_reused)
            print('  📝 Note: ' + ', '.join(within_reused) +
                  (' is' if saved == 1 else ' are') +
                  ' already committed to an earlier team in this track — reused here instead of ' +
                  ('a new roster slot' if saved == 1 else str(saved) + ' new roster slots') +
                  ' to keep leveling investment down.')
        if cross_reused_tracks:
            for n, other_tracks in sorted(cross_reused_tracks.items()):
                print('  🔗 Cross-track win: ' + n + ' is already committed in the ' +
                      ' & '.join(other_tracks) + ' track' + ('' if len(other_tracks) == 1 else 's') +
                      ' — reusing here means no extra roster slot for the whole event.')
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

    # Shared across tracks, in the order tracks are processed below, so later
    # tracks get reuse credit (and cross-track notes) for characters already
    # committed in an earlier track — see optimal_coverage / analyse_track.
    global_usage = {}
    global_char_tracks = {}

    tracks = config.get('tracks', [])
    for track in tracks:
        analyse_track(track['name'], track, chars, global_usage, global_char_tracks)

    multi_track = {n: sorted(tset) for n, tset in global_char_tracks.items() if len(tset) > 1}
    if multi_track:
        print('\n' + '='*65)
        print('  CROSS-TRACK INVESTMENT SUMMARY')
        print('='*65)
        print('  These characters cover objectives in more than one track —')
        print('  leveling them is worth more than a single-track pick:')
        print()
        for n in sorted(multi_track, key=lambda n: (-len(multi_track[n]), n)):
            print('  ' + char_line(n, chars, '  * ') + '  — used in: ' + ' & '.join(multi_track[n]))

    def is_healer(name):
        c = chars[name]
        return c.get('Healer', 'N') == 'Y' or c.get('Mechanic', 'N') == 'Y'

    def is_tank(name):
        c = chars[name]
        return c.get('Terminator_Armour', 'N') == 'Y' or c.get('Mk_X_Gravis', 'N') == 'Y'

    def is_selfheal_or_dr(name):
        return (chars[name].get('Self_Heal', 'N') == 'Y'
                or name in DAMAGE_REDUCTION or name in ABILITY_TANKS)

    def print_leaderboard(title, usage_subset):
        print('\n  ' + title + ':')
        repeats = {n: c for n, c in usage_subset.items() if c > 1}
        if not repeats:
            print('    None used more than once this event.')
            return
        for n in sorted(repeats, key=lambda n: (-repeats[n], n)):
            times = repeats[n]
            print('  ' + char_line(n, chars, '  * ') + '  — used ' + str(times) + ' times')

    # These four categories intentionally overlap (e.g. Toth is both a Tank
    # and a Self-Heal/DR pick) — they mirror the four Monthly Plan video
    # cards, which are independent tallies rather than a mutually exclusive
    # partition. Each is capped to its top 4 by usage count.
    healer_usage = {n: c for n, c in global_usage.items() if is_healer(n)}
    tank_usage   = {n: c for n, c in global_usage.items() if is_tank(n)}
    sh_dr_usage  = {n: c for n, c in global_usage.items() if is_selfheal_or_dr(n)}

    print('\n' + '='*65)
    print('  CHAMPION USAGE LEADERBOARD (whole event, used more than once)')
    print('='*65)
    print_leaderboard('Healers (Healers + Mechanics)', healer_usage)
    print_leaderboard('Tanks', tank_usage)
    print_leaderboard('Self-Heal / Damage Reduction', sh_dr_usage)
    print_leaderboard('Most used overall', global_usage)

    print('\n' + '='*65)
    print('  ANALYSIS COMPLETE')
    print('='*65 + '\n')

    builtins.print = orig_print

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('>>> Saved to: ' + out_path)

if __name__ == '__main__':
    main()