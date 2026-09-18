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
import re
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


# A character with a heal or repair action spends its turn on it: "you can't heal and attack, a heal is
# like a repeatable active" (owner, September 2026). Eleven characters have one, and Baldr's Healing Balms
# rides on his, so his crit buff costs him his attack too. The model tries the five both ways and keeps
# whichever is better for the axis being asked about, the same way the map only uses an active when it
# beats a normal attack - and the same way this page already picks a different five for each axis.
HEAL_TRAITS = ('Healer', 'Mechanic')


def heals(member):
    return bool(set(member['traits']) & set(HEAL_TRAITS))


def costs_the_turn(rows, who):
    """the row indices that only happen if the character spends its action healing. `who` is every
    character with a heal or repair action, and it has to be gathered across both sides of the CSV,
    because the trait itself is a Defence row and the abilities riding on it are not."""
    return {i for i, r in enumerate(rows)
            if 'healaction' in r['Effect']
            or (r['Name'] in who and re.search(r'action to (heal|repair)', r['Ability_Text'] or '', re.I))}


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


def attack_tokens(five, rows, UA, lv, tier_key, order, drop=()):
    """{member name: [token]} - every Attack-side buff the five hands out inside itself. `drop` is the
    rows that do not happen because their owner is attacking this turn instead of healing."""
    out = {m['name']: [] for m in five}
    inside = {m['name'] for m in five}
    for i, r in enumerate(rows):
        if i in drop or r['Name'] not in inside or not _row_ok(r, tier_key):
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


def defence_rows(five, rows, UA, SU, lv, tier_key, order, drop=()):
    """{member name: [(ds first turn, ds later, regen, attacker filter)]} from the five's Defence rows"""
    out = {m['name']: [] for m in five}
    inside = {m['name'] for m in five}
    for i, r in enumerate(rows):
        if i in drop or r['Name'] not in inside or not _row_ok(r, tier_key):
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


# The Mythic ability every machine has. Six of the eleven put a percentage on your damage or on what the
# enemy takes, and those are in guild_raid.MOW_BUFF. The other five are defensive, and the Guild Raid model
# had no use for them because it is a damage run - so they are read here. All five are the Mythic ability
# at its top level, like the offensive ones.
MOW_DEF = {
    'Galatian': ('WisdomOfTheAncients', 'dmgReductionPct'),
    'Forgefiend': ('ContemptuousDisregard', 'dmgReductionPct'),
    "Tson'ji": ('ElectrochaffBackups', 'dmgReductionPct'),
    'Storm Speeder': ('MastersOfManoeuvre', 'dmgReductionPct'),
    # the only one that is not a flat reduction: a shield worth half a character's Health, refreshed every
    # turn it Crits or hits something standing on Fire. With gear on and everything triggered, that is
    # every turn, so it is read as a shield the team simply has.
    'Exorcist': ('ShieldOfFaith', 'shieldPct'),
}


def mow_defence(g, mow):
    """(a defence spec every member gets, a share of max Health shielded each turn) from the machine's
    Mythic ability"""
    got = MOW_DEF.get(mow['name']) if mow else None
    if not got:
        return None, 0.0, None
    ab = gr._ability(g, got[0])
    v = (gr.bossval(ab, got[1], gr.MYTHIC_ABILITY_LEVEL) or 0.0) if ab else 0.0
    if not v:
        return None, 0.0, None
    name = (ab.get('name') or got[0])
    if got[1] == 'shieldPct':
        return None, v / 100, f'{name}: a shield worth {v:.0f}% of Health every turn'
    ds = bm.new_ds()
    ds['pct'].append((1 - v / 100, 'all', None))
    return ds, 0.0, f'{name}: the five take {v:.0f}% less damage'


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
    __slots__ = ('u', 'spec', 'armour', 'rnd0', 'rest0', 'rows', 'shield', '_cache')

    def __init__(self, u, spec, armour, rnd0, rest0, rows, shield=0.0):
        self.u, self.spec, self.armour = u, spec, armour
        self.rnd0, self.rest0, self.rows = rnd0, rest0, rows
        self.shield = shield * u['hp']          # a Machine of War's shield, as health it gets back each turn
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
            if self.shield:
                regen = regen or dict(turn=0.0, hit=0.0, shield=0.0, shield_first=0.0)
                regen['shield'] = regen.get('shield', 0.0) + self.shield
            if regen:
                regen['limit'] = CAP
            got = self._cache[key] = (rnd, rest, regen)
        return got


def make(member, five, toks, drows, sp, rnd, rest, lv, tier_key, buff=None, mow_ds=None, shield=0.0):
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
    r0, r1 = rnd[member['name']], rest[member['name']]
    if mow_ds:
        r0, r1 = bm.merge_defence(r0, mow_ds), bm.merge_defence(r1, mow_ds)
    return Fighter(u, spec, armour, r0, r1, drows, shield)


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

    # Which support rows only happen if their owner spends the turn healing.
    action_heals = {r['Name'] for r in arows + drows_all if 'healaction' in r['Effect']}
    acost, dcost = costs_the_turn(arows, action_heals), costs_the_turn(drows_all, action_heals)

    def five_of(members, buff=None, healing=(), mow_ds=None, shield=0.0):
        adrop = {i for i in acost if arows[i]['Name'] not in healing}
        ddrop = {i for i in dcost if drows_all[i]['Name'] not in healing}
        toks = attack_tokens(members, arows, UA, lv, tier_key, hit_order, adrop)
        drows = defence_rows(members, drows_all, UA, SU, lv, tier_key, frail_order, ddrop)
        return [make(m, members, toks[m['name']], drows[m['name']], sp, rnd, rest, lv, tier_key, buff,
                     mow_ds, shield) for m in members]

    # The yardstick: every character standing among its own faction, measured against the others doing
    # the same. This is the map's "typical character" moved up a level, and it is computed once. Its
    # healers heal, because that is what a faction standing together looks like.
    pool = []
    for faction, members in roster.items():
        pool += five_of(members, healing={m['name'] for m in members if heals(m)})
    if verbose:
        print(f'Yardstick: {len(pool)} characters, each buffed by their own faction.')

    # The "alone" half of the synergy number has to face the same yardstick as the buffed half, or the
    # comparison is measuring the yardstick rather than the buffs. Alone there is nobody to heal, so
    # every one of the five attacks.
    solo = {n: scores(f, pool) for n, f in bare.items()}

    def axes(members, healing, buff=None, rate=0.0, mow_ds=None, shield=0.0):
        """(damage, toughness, per-member scores) for one five with one choice of who is healing"""
        per = {m['name']: scores(f, pool)
               for m, f in zip(members, five_of(members, buff, healing, mow_ds, shield))}
        hit = [p for n, p in per.items() if n not in healing]
        dmg = TEAM / (sum(1 / p[0] for p in hit) + rate) if (hit or rate) else CAP
        return dmg, st.mean(p[1] for p in per.values()), per

    out = {}
    for faction, members in sorted(roster.items()):
        mow = mow_of(g, faction)
        buff = gr.mow_buff(g, mow, lv, tier_key, TRIG) if mow else None
        mow_ds, shield, mow_note = mow_defence(g, mow)
        rate = mow_rate(g, mow, pool, members[0]['alliance'], lv) if mow else 0.0
        teams = []
        for combo in (itertools.combinations(members, TEAM) if len(members) >= TEAM else ()):
            combo = list(combo)
            who = [m['name'] for m in combo if heals(m)]
            branches = [frozenset(c) for k in range(len(who) + 1) for c in itertools.combinations(who, k)]
            plain = [axes(combo, h) for h in branches]
            bd, bt = min(plain, key=lambda x: x[0]), max(plain, key=lambda x: x[1])
            row = dict(names=[m['name'] for m in combo],
                       benched=next((m['name'] for m in members if m not in combo), None),
                       dmg=bd[0], tough=bt[1],
                       healing=sorted(branches[plain.index(bt)]),
                       per={n: dict(d=round(bd[2][n][0], 3), t=round(bt[2][n][1], 3)) for n in bd[2]})
            alone = [solo[m['name']] for m in combo]
            row['dmg_alone'] = TEAM / sum(1 / p[0] for p in alone)
            row['tough_alone'] = st.mean(p[1] for p in alone)
            if mow:
                withm = [axes(combo, h, buff, rate, mow_ds, shield) for h in branches]
                row['dmg_mow'] = min(x[0] for x in withm)
                row['tough_mow'] = max(x[1] for x in withm)
            else:
                row['dmg_mow'] = row['tough_mow'] = None
            teams.append(row)
        # A signature trait is one every member carries. It falls out of the data rather than being
        # listed by hand, so whatever the game adds next is picked up - and it is worth saying on the
        # page that carrying one is not a reward for going pure: you get it in any team.
        common = sorted(set.intersection(*[set(m['traits']) for m in members]))
        out[faction] = dict(n=len(members), roster=[m['name'] for m in members], teams=teams,
                            alliance=members[0]['alliance'], signature=common,
                            ranged=sum(1 for m in members if any(w['kind'] == 'ranged' for w in m['weapons'])),
                            healer=sorted({t for m in members for t in m['traits'] if t in HEAL_TRAITS}),
                            mow=dict(name=mow['name'], buff=(buff or {}).get('name'),
                                     note=(buff or {}).get('note', ''), defence=mow_note,
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
        rows.append((faction, d['n'], bd['dmg'], bd['dmg_alone'] / bd['dmg'] - 1, bt['tough'],
                     bt['tough'] / bt['tough_alone'] - 1,
                     min((t['dmg_mow'] for t in d['teams']), default=None) if d['mow'] else None,
                     max((t['tough_mow'] for t in d['teams']), default=None) if d['mow'] else None,
                     bd['benched'], bt['benched']))
    print(f"\n{'faction':22} {'n':>2} {'damage':>7} {'synergy':>8} {'tough':>7} {'synergy':>8} "
          f"{'dmg+mow':>8} {'tgh+mow':>8}  benched (dmg / tough)")
    for f, n, dmg, ds, tg, ts, dm, tm, bd, bt in sorted(rows, key=lambda r: r[2]):
        bench = f'{bd} / {bt}' if bd else ''
        m1 = f'{dm:>8.2f}' if dm else f'{"-":>8}'
        m2 = f'{tm:>8.2f}' if tm else f'{"-":>8}'
        print(f'{f:22} {n:>2} {dmg:>7.2f} {ds:>+7.1%} {tg:>7.2f} {ts:>+7.1%} {m1} {m2}  {bench}')


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
