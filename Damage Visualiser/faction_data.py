"""
faction_data.py - every faction as a five that plays together.

The Roster Battle Map asks what one character does in a duel, where nobody buffs anybody. This asks the
same two questions - how many attacks to kill a typical character, how many to be killed - of a whole
faction fielded together, where the buffs are the entire point. It is the Arena and Tournament Arena
question: five of one faction, plus a Machine of War.

What it counts that the map does not:

- **The mates' support**, both sides of it. Every Attack and Defence row in `support_abilities.csv` whose
  owner is in the five and whose `Receives` admits the target, run through `support_model.buffed()` and
  `support_model.defence_for()` exactly as the Support Map runs them.
- **The faction-locked clauses**, which are the real reward for going pure and are worth nothing on the
  map: Asmodai's and Baraqiel's +Damage beside a Dark Angel, Forcas's "for each adjacent", the Winged
  Prime's Hormagaunts arriving once per Synapse ally, and the Norn Crown naming Summons. These live in
  `guild_raid.py` and are imported from there so there is one definition of each, not two.

The yardstick is the same idea as the map's "typical character", moved up a level: every one of the 117
buffed by its own faction mates, then measured against each other. A faction's number is therefore how it
does against other factions playing together, not against loose characters.

Two axes, aggregated the way the fight aggregates them:

- **Damage** adds up as *rates*. Five characters attacking together kill a target in `1 / sum(1/k_i)`
  team-attacks, so the faction's figure is `5 / sum(1/k_i)` - the same "attacks to kill" unit as the map,
  read as what an average member of the five needs when all five are swinging.
- **Toughness** adds up as *time*. Focus fire kills a team one at a time, so wiping the five takes
  `sum(k_i)` attacks and the faction's figure is the mean.

    python -X utf8 faction_data.py              # the table
    python -X utf8 faction_data.py --json       # and write faction_data.json for the page

See PLAN.md, "Faction comparison".
"""
import argparse
import itertools
import json
import os
import statistics as st

import build_map as bm
import guild_raid as gr
import support_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(HERE, 'faction_data.json')

TEAM = 5                          # Arena and Tournament Arena field five, plus a Machine of War
CAP = sm.HORIZON_TURNS * bm.ATTACKS_PER_TURN   # "survives 10+ turns": stop there, as the Support Map does

# How many of the four team-mates a buff of each reach actually lands on. 'adjacent' is
# guild_raid.ADJACENT_ALLIES so every adjacency question in the project answers to one number; '2 hexes'
# reaches the whole formation at this size, and so do team and target buffs.
REACH = {'adjacent': gr.ADJACENT_ALLIES, '2 hexes': 4, 'team': 4, 'target': 4, 'one': 1, 'next attack': 1}

# The one setting, the same one the Guild Raid page uses: maxed Mythic, level 60 abilities, standard gear
# with relics, actives used, everything triggered.
TRIG, ACT, GEAR = True, True, True


# ---------------------------------------------------------------- the buffs a five gives itself
def _row_ok(r, tier_key):
    if (r['Source'] == 'Active' or r['Condition'] == 'active') and not ACT:
        return False
    if r['Condition'] == 'trig' and not TRIG:
        return False
    return not (r['Source'] == 'Relic' and not (tier_key == 'mythic' and GEAR))


def _reach_trim(elig, reach, order):
    """a buff with a reach shorter than the team picks its receivers: you buff the hitters and you shield
    the fragile, so `order` is the ranking the caller wants and the top `reach` of them get it."""
    n = REACH[reach]
    if len(elig) <= n:
        return elig
    return sorted(elig, key=lambda m: order[m['name']])[:n]


def attack_tokens(five, rows, UA, lv, tier_key, order):
    """{member name: [token]} - every Attack-side buff the five hands out inside itself"""
    out = {m['name']: [] for m in five}
    inside = {m['name'] for m in five}
    for r in rows:
        if r['Name'] not in inside or not _row_ok(r, tier_key):
            continue
        ab, relic = sm.row_ability(UA, r)
        got = {}
        for m in five:
            if m['name'] == r['Name'] or not sm.matches(m, r['Receives']):
                continue
            toks = sm.tokens_for(r, m, ab, relic, lv, TRIG)
            if toks:
                got[m['name']] = toks
        for m in _reach_trim([m for m in five if m['name'] in got], r['Reach'], order):
            out[m['name']] += got[m['name']]
    return out


def defence_rows(five, rows, UA, SU, lv, tier_key, order):
    """{member name: [(ds first turn, ds later, regen, attacker filter)]} from the five's Defence rows"""
    out = {m['name']: [] for m in five}
    inside = {m['name'] for m in five}
    for r in rows:
        if r['Name'] not in inside or not _row_ok(r, tier_key):
            continue
        ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(UA, r)
        sup = SU[r['Name']]
        got = {}
        for m in five:
            if m['name'] == r['Name'] or not sm.matches(m, r['Receives']):
                continue
            d = sm.defence_for(r, sup, m, ab, relic, lv, TRIG)
            if d:
                got[m['name']] = d
        for m in _reach_trim([m for m in five if m['name'] in got], r['Reach'], order):
            out[m['name']].append(got[m['name']])
    return out


# ---------------------------------------------------------------- what a faction ally unlocks
def own_clauses(member, five, lv):
    """the character's own faction-locked clauses, as effects on its normal attacks. These are the real
    reward for going pure and the Roster Battle Map, being a duel, scores every one of them at zero."""
    eff = []
    v, scope = gr.faction_flat(member, five, lv, TRIG)
    if v:
        eff.append(dict(kind='flat', scope=scope, vs=None, value=v))
    for value, how, scope in gr.per_adjacent(member, five, lv):
        eff.append(dict(kind='pct' if how == 'pct' else 'flat', scope=scope, vs=None, value=value))
    return eff


def team_summons(member, five, lv, tier_key):
    """the character's summons as the five changes them: more of them per ally of the right kind (the
    Winged Prime's Hormagaunts), and hitting harder if the five holds the Norn Crown."""
    got = bm.summons_of(member, lv)
    if not got:
        return None
    per_ally = gr.SUMMON_PER_ALLY.get(member['name'])
    bonus = 0.0
    neuro = next((m for m in five if m['name'] == 'Neurothrope'), None)
    if neuro and tier_key == 'mythic' and GEAR and (neuro.get('relic') or {}).get('name') == 'Norn Crown':
        bonus = sm.value(neuro['relic']['ability'], 'extraDmg', bm.RELIC_LEVEL, True)   # the Crown names Summons
    out = []
    for n, npc, dmg, kind in got:
        if per_ally and kind == 'passive':
            trait, capvar = per_ally
            cap = bm.ability_value(member.get(kind) or {}, capvar, lv) or n
            n = min(sum(1 for m in five if trait in m['traits']), max(cap, n))
        out.append((n, npc, dmg + bonus, kind))
    return out


# ---------------------------------------------------------------- the Machine of War slot
# Arena and Tournament Arena field five characters plus a Machine of War, and eleven of the 21 factions
# have one. What it brings is read from guild_raid.py so there is one definition: its Mythic ability, and
# the attack it fires every round.
#
# Two honest limits, both stated on the page. **Six of the eleven machines are defensive** - the Galatian,
# the Exorcist, the Forgefiend, the Tson'ji and the Storm Speeder shield or heal rather than hit, and
# nothing reads those Mythic abilities yet - so a machine never moves the Toughness axis and those
# factions' machine column is a floor, not a figure. And the machine is a sixth attacker, not a sixth
# body: it is never counted as something the enemy has to kill.
def mow_of(g, faction):
    return next((m for m in gr.machines(g)
                 if gr.FACTION_ID.get(m['factionId'], m['factionId']) == faction), None)


def mow_effect(buff, member):
    """the Mythic ability as a +% on this member's attacks, or None. 'taken' puts the percentage on the
    enemy and 'dmg' puts it on your own character; against one target both come to the same multiplier,
    so both are read the same way, on the attacks the ability names."""
    if not buff or (buff['who'] != 'all' and buff['who'] not in member['traits']):
        return None
    return dict(kind='pct', scope=buff['only'] or 'all', vs=None, value=buff['pct'])


def mow_attacker(mow, alliance):
    """the machine as an attacker, for the Defence buffs that only work against some attackers. It has no
    character traits and no weapon of its own, so a "+Armour against Psykers" row does not answer it."""
    return dict(name=mow['name'], traits=set(), alliance=alliance, weapons=[])


def mow_round(g, mow, d, ds, lv):
    """what the machine puts into this defender in one round. The round or two a machine waits for its
    cooldown is not counted: over a kill that takes several turns it is worth less than it costs to say."""
    out = 0.0
    for shot in gr.MOW_EVERY_ROUND.get(mow['name'], []):
        part = _mow_part(g, shot, lv)
        if part:
            out = max(out, bm.part_vs_defence(part, d, ds, False)[0])        # the best one, every round
    for shot in gr.MOW_SHOTS.get(mow['name'], []):
        part = _mow_part(g, shot, lv)
        if part:
            out += bm.part_vs_defence(part, d, ds, False)[0] * shot[1]       # a rate, not a round number
    return out


def _mow_part(g, shot, lv):
    ab_id, _, dt, hits = (list(shot) + [None, None])[:4]
    ab = gr._ability(g, ab_id)
    if not ab or 'minDmg' not in (ab.get('variables') or {}):
        return None
    part = gr._part(ab, min(lv, gr.MOW_LEVELS), '', dt, rarity=True)
    if hits:
        part['hits'] = hits
    return part


# ---------------------------------------------------------------- a member, ready to fight
def admits(filt, a):
    """does an attacker-conditional Defence buff work against this attacker?"""
    flt, vs = filt
    if flt is None:
        return True
    if flt == 'psychic':
        return any(w['type'] in ('Psychic', 'Direct') for w in a['weapons'])
    return bool(vs & (a['traits'] | {a['alliance']}))


class Fighter:
    """one character with its mates' buffs on: what it attacks with, and what it is defended by. The
    defence is resolved per attacker because several buffs only work against Psykers or against Chaos."""
    __slots__ = ('u', 'spec', 'armour', 'rnd0', 'rest0', 'rows', '_cache')

    def __init__(self, u, spec, armour, rnd0, rest0, rows):
        self.u, self.spec, self.armour = u, spec, armour
        self.rnd0, self.rest0, self.rows = rnd0, rest0, rows
        self._cache = {}

    def against(self, a):
        key = tuple(i for i, row in enumerate(self.rows) if admits(row[3], a))
        got = self._cache.get(key)
        if got is None:
            rnd = bm.merge_defence(self.rnd0, *(self.rows[i][0] for i in key))
            rest = bm.merge_defence(self.rest0, *(self.rows[i][1] for i in key))
            regen = None
            for i in key:
                if self.rows[i][2]:
                    regen = regen or dict(turn=0.0, hit=0.0, shield=0.0, shield_first=0.0)
                    for k, v in self.rows[i][2].items():
                        regen[k] = regen.get(k, 0.0) + v
            if regen:
                regen['limit'] = CAP
            got = self._cache[key] = (rnd, rest, regen)
        return got


def make(member, five, toks, drows, sp, rnd, rest, lv, tier_key, buff=None):
    """a Fighter: the member with its five's buffs, its own faction clauses, its team summons, and its
    Machine of War's Mythic ability if the faction has one and this call is counting it"""
    u = dict(member)
    u['summons'] = team_summons(member, five, lv, tier_key)
    extra = own_clauses(member, five, lv)
    if (e := mow_effect(buff, member)):
        extra.append(e)
    if extra:
        eff, desc = (list(u['ps'][0]), list(u['ps'][1])) if u.get('ps') else ([], [])
        u['ps'] = (eff + extra, desc)
    spec = sp['active'].get(member['name']) if ACT else None
    u, spec, armour = sm.buffed(u, toks, spec, GEAR) if toks else (u, spec, 0.0)
    return Fighter(u, spec, armour, rnd[member['name']], rest[member['name']], drows)


def kills(atk, dfn):
    """attacks for one Fighter to kill another, stopped at the 10-turn horizon"""
    d = dfn.u
    if atk.armour:
        d = dict(d, arm=max(d['arm'] - atk.armour, 0.0))
    rnd, rest, regen = dfn.against(atk.u)
    return min(bm.attacks_to_kill(atk.u, d, TRIG, atk.spec, rnd, rest, regen)[0], CAP)


def health(d, ds):
    """the health a defender actually has to lose, the way attacks_to_kill counts it"""
    hp = d['hp'] * (ds['hpmult'] if ds else 1) + (ds['heal'] if ds else 0)
    return hp * 2 if (TRIG and 'Ambush' in d['traits']) else hp


def mow_rate(g, mow, pool, alliance, lv):
    """1 / (the turns the machine alone needs to kill a typical character)"""
    a = mow_attacker(mow, alliance)
    ks = []
    for dfn in pool:
        rnd, rest, _ = dfn.against(a)
        per = mow_round(g, mow, dfn.u, rest, lv)
        ks.append(health(dfn.u, rnd) / per if per > 0 else CAP)
    return 1 / min(st.median(ks), CAP)


def scores(f, pool):
    """(its Damage against the yardstick, its Toughness against the yardstick)"""
    return (st.median(kills(f, d) for d in pool),
            st.median(kills(a, f) for a in pool))


# ---------------------------------------------------------------- the run
def build(tier=2, verbose=True):
    bm.set_tier(bm.TIERS[tier])
    tier_key = bm.TIERS[tier]['key']
    g, units = bm.load()
    actives = bm.sync_rows(bm.ACTIVES_CSV, bm.ACTIVE_COLS, 'Active', units, bm.draft_active, 'active_abilities.csv')
    passives = bm.sync_rows(bm.PASSIVES_CSV, bm.PASSIVE_COLS, 'Passive', units, bm.draft_passive,
                            'passive_abilities.csv')
    relics = bm.sync_relics(g, units)
    specs = bm.build_specs(units, actives, passives, relics)
    lv = bm.ABILITY_LEVELS[1]
    arows, drows_all = sm.load_rows('Attack'), sm.load_rows('Defence')
    U, sp, rnd, rest = sm.setting_units(units, specs, lv, TRIG, ACT, GEAR)
    UA = {u['name']: u for u in units}
    SU = {u['name']: u for u in U}

    roster = {}
    for u in U:
        roster.setdefault(u['faction'], []).append(u)

    # Bare fighters first: no mates at all. They are the "alone" half of the synergy number, and their
    # scores against each other give the ranking that decides who a short-reach buff lands on.
    bare = {u['name']: Fighter(u, sp['active'].get(u['name']) if ACT else None, 0.0,
                               rnd[u['name']], rest[u['name']], []) for u in U}
    duel = {n: scores(f, list(bare.values())) for n, f in bare.items()}
    hit_order = {n: v[0] for n, v in duel.items()}          # lowest attacks-to-kill first: buff the hitters
    frail_order = {n: v[1] for n, v in duel.items()}        # lowest toughness first: shield the fragile

    def five_of(members, buff=None):
        toks = attack_tokens(members, arows, UA, lv, tier_key, hit_order)
        drows = defence_rows(members, drows_all, UA, SU, lv, tier_key, frail_order)
        return [make(m, members, toks[m['name']], drows[m['name']], sp, rnd, rest, lv, tier_key, buff)
                for m in members]

    # The yardstick: every character standing among its own faction, measured against the others doing
    # the same. This is the map's "typical character" moved up a level, and it is computed once.
    pool = []
    for faction, members in roster.items():
        pool += five_of(members)
    if verbose:
        print(f'Yardstick: {len(pool)} characters, each buffed by their own faction.')

    # The "alone" half of the synergy number has to face the same yardstick as the buffed half, or the
    # comparison is measuring the yardstick rather than the buffs.
    solo = {n: scores(f, pool) for n, f in bare.items()}

    out = {}
    for faction, members in sorted(roster.items()):
        mow = mow_of(g, faction)
        buff = gr.mow_buff(g, mow, lv, tier_key, TRIG) if mow else None
        rate = mow_rate(g, mow, pool, members[0]['alliance'], lv) if mow else 0.0
        teams = []
        for combo in (itertools.combinations(members, TEAM) if len(members) >= TEAM else ()):
            combo = list(combo)
            per = [scores(f, pool) for f in five_of(combo)]
            per_mow = [scores(f, pool) for f in five_of(combo, buff)] if buff else per
            alone = [solo[m['name']] for m in combo]
            teams.append(dict(
                names=[m['name'] for m in combo],
                benched=next((m['name'] for m in members if m not in combo), None),
                dmg=TEAM / sum(1 / p[0] for p in per),
                tough=st.mean(p[1] for p in per),
                dmg_mow=TEAM / (sum(1 / p[0] for p in per_mow) + rate) if mow else None,
                dmg_alone=TEAM / sum(1 / p[0] for p in alone),
                tough_alone=st.mean(p[1] for p in alone),
                per={m['name']: dict(d=round(p[0], 3), t=round(p[1], 3)) for m, p in zip(combo, per)}))
        out[faction] = dict(n=len(members), roster=[m['name'] for m in members], teams=teams,
                            mow=dict(name=mow['name'], buff=(buff or {}).get('name'),
                                     note=(buff or {}).get('note', ''),
                                     solo=round(1 / rate, 3) if rate else None) if mow else None)
        if verbose and teams:
            best = min(teams, key=lambda t: t['dmg'])
            print(f'  {faction:22} {len(teams)} five(s): best damage {best["dmg"]:.2f}')
    return out, g['version']


def report(data):
    rows = []
    for faction, d in data.items():
        if not d['teams']:
            continue
        bd = min(d['teams'], key=lambda t: t['dmg'])
        bt = max(d['teams'], key=lambda t: t['tough'])
        bw = min(d['teams'], key=lambda t: t['dmg_mow'] or 9e9) if d['mow'] else None
        rows.append((faction, d['n'], bd['dmg'], bd['dmg_alone'] / bd['dmg'] - 1, bt['tough'],
                     bt['tough'] / bt['tough_alone'] - 1, bw['dmg_mow'] if bw else None,
                     (d['mow'] or {}).get('name'), bd['benched'], bt['benched']))
    print(f"\n{'faction':22} {'n':>2} {'damage':>7} {'synergy':>8} {'tough':>7} {'synergy':>8} "
          f"{'+machine':>9}  benched (dmg / tough)")
    for f, n, dmg, ds, tg, ts, dm, mw, bd, bt in sorted(rows, key=lambda r: r[2]):
        bench = f'{bd} / {bt}' if bd else ''
        mach = f'{dm:>9.2f}' if dm else f'{mw or "-":>9}'
        print(f'{f:22} {n:>2} {dmg:>7.2f} {ds:>+7.1%} {tg:>7.2f} {ts:>+7.1%} {mach}  {bench}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true', help='write faction_data.json as well')
    args = ap.parse_args()
    data, version = build()
    report(data)
    if args.json:
        with open(OUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(dict(version=version,
                           setting=dict(tier='mythic', level=bm.ABILITY_LEVELS[1], trig=TRIG, act=ACT,
                                        gear=GEAR, adjacent=gr.ADJACENT_ALLIES, cap=CAP),
                           factions=data), f, indent=1)
        print(f'\nWrote {os.path.basename(OUT_JSON)}.')


if __name__ == '__main__':
    main()
