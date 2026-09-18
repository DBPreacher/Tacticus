"""
calc_data.py - the numbers the Guild Raid page's Calculate button needs.

The page ships precomputed best-fives, but "score the five I picked" cannot be precomputed: 117 characters
make 138 million teams, and a team's damage does not come apart into per-character pieces (Laviscus's
Outrage and the buffs compound, so adding or multiplying per-character values is 40-80% out - measured).

So the page scores a team itself. Everything hard stays here in Python: every ability is already resolved
to plain numbers by build_map.py, so what ships is a character's weapons, traits, gear, the effects of its
passive, the parts of its active, and the buff tokens it hands the rest of the team. The page only has to
do the arithmetic, and it checks itself on load against exact scores from guild_raid.py (VECTORS below).

Used by build_guild.py. See INSTRUCTIONS.md ("Guild Raid", the Calculate button).
"""
import hashlib
import os
import random
import build_map as bm
import support_model as sm
import guild_raid as gr

SETTING = ('mythic', 60, True, True, True)     # tier, ability level, traits, actives, gear
N_VECTORS = 50                                 # exact scores the page checks itself against


# Everything that can change an answer. brute_all.js stamps this into best_fives.json and build_guild.py
# refuses to publish a run whose fingerprint no longer matches, so a game update or a change to the model
# can't quietly leave two-hour-old best fives on the page.
FINGERPRINT_FILES = ('active_abilities.csv', 'passive_abilities.csv', 'relic_abilities.csv',
                     'support_abilities.csv', 'build_map.py', 'support_model.py', 'guild_raid.py',
                     'calc_data.py', 'calc.js', 'brute.js')


def fingerprint(g):
    """one short string for the game data and every file that decides what a team scores"""
    h = hashlib.sha1(g['version'].encode())
    here = os.path.dirname(os.path.abspath(__file__))
    for name in FINGERPRINT_FILES:
        path = os.path.join(here, name)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                h.update(name.encode())
                h.update(hashlib.sha1(f.read()).digest())
    return h.hexdigest()[:16]


def _weapon(w):
    return dict(k=w['kind'], t=w['type'], h=w['hits'], p=w['pierce'], r=w['range'])


def _part(p):
    return dict(d=round(p['dmg'], 1), h=p['hits'], t=p['type'], c=bool(p.get('crit', True)))


def _effect(e):
    out = dict(k=e['kind'], s=e['scope'])
    if e.get('value') is not None:
        out['v'] = round(e['value'], 2)
    if e.get('vs'):
        out['vs'] = sorted(e['vs'])
    if e.get('vsnot'):
        out['vsnot'] = sorted(e['vsnot'])
    if e.get('part'):
        out['p'] = _part(e['part'])
    if e.get('part_big'):
        out['pb'] = _part(e['part_big'])
    return out


def characters(U, sp, g, lv, trig=True):
    """every character as the page needs it: stats, weapons, traits, gear, passive, active, summons"""
    out = []
    for u in U:
        eff = (u['ps'] or ([], []))[0]
        gear = u.get('g') or {}
        spec = sp['active'].get(u['name'])
        c = dict(n=u['name'], f=u['faction'], a=u['alliance'], dmg=round(u['dmg'], 1), arm=round(u['arm'], 1),
                 w=[_weapon(w) for w in u['weapons']], tr=sorted(u['traits']),
                 g=dict(cc=gear.get('cc', 0), cd=gear.get('cd', 0), bc=gear.get('bc', 0), bd=gear.get('bd', 0)),
                 ps=[_effect(e) for e in eff],
                 pg=[_effect(e) for e in (u.get('pg') or [])])
        # an active with no damage parts of its own still counts: several are just a normal attack
        if spec and (spec.get('parts') or spec.get('normal') in ('Y', 'PCT') or spec.get('same_turn')):
            c['sp'] = dict(p=[_part(p) for p in spec['parts']], same=bool(spec.get('same_turn')),
                           normal=spec.get('normal'), weapon=spec.get('weapon'), pct=spec.get('pct'),
                           cap=spec.get('cap'), flat=spec.get('flat'),
                           bonus=_part(spec['bonus']) if spec.get('bonus') else None,
                           gx=[_effect(e) for e in (spec.get('gear') or [])] or None)
        if gr.MODEL_OWN.get(u['name']):
            c['drop'] = sorted(gr.MODEL_OWN[u['name']])    # counted elsewhere (the Neuroparasite's cap)
        if (u.get('relic') or {}).get('name'):
            c['rel'] = u['relic']['name']
        act = ((u.get('ability') or {}).get('constants') or {}).get('cooldownTurns')
        if act not in (None, ''):
            c['cd'] = int(float(act))
        # the handful of characters whose numbers grow through the battle, resolved here so the page
        # doesn't have to know their names
        ab = u['passive'] or {}
        if u['name'] in gr.RAMP:
            c['rampPct'] = sm.value(u['ability'] or {}, gr.RAMP[u['name']], lv)
        if u['name'] in gr.RAMP_FLAT:
            c['rampFlat'] = sm.value(u['ability'] or {}, gr.RAMP_FLAT[u['name']], lv)
        if u['name'] in gr.DIRECT:
            c['direct'] = list(gr.DIRECT[u['name']])
        if u['name'] in gr.PSYCHIC_HITS:
            c['psyCap'] = float(((u['ability'] or {}).get('constants') or {}).get(gr.PSYCHIC_HITS[u['name']]) or 99)
        if u['name'] in gr.RAMP_TEAM:
            c['rampTeam'] = sm.value(ab, gr.RAMP_TEAM[u['name']], lv)
        if u['name'] in gr.RAMP_STACK:
            var, capvar = gr.RAMP_STACK[u['name']]
            c['rampStack'] = [sm.value(ab, var, lv), float((ab.get('constants') or {}).get(capvar) or 99)]
        # what a faction ally unlocks, resolved to numbers here so the page only has to count allies
        if u['name'] in gr.NO_COOLDOWN:
            c['noCd'] = gr.NO_COOLDOWN[u['name']]
        if u['name'] in gr.FACTION_FLAT:
            faction, kind, var, scope, alone, allied, needs_trig = gr.FACTION_FLAT[u['name']]
            ab2 = u.get(kind) or {}
            base = bm.ability_value(ab2, var, lv) or 0.0
            if not (needs_trig and not trig):
                c['facFlat'] = [faction, scope, round(base * alone, 1), round(base * allied, 1)]
        if u['name'] in gr.PER_ADJACENT:
            adj = []
            for who, kind, var, how, scope in gr.PER_ADJACENT[u['name']]:
                ab2 = u.get(kind) or {}
                if var in (ab2.get('variables') or {}):
                    adj.append([who, how, scope, round(bm.ability_value(ab2, var, lv) or 0.0, 2)])
            if adj:
                c['perAdj'] = adj
        if u['name'] in gr.SUMMON_PER_ALLY:
            trait, capvar = gr.SUMMON_PER_ALLY[u['name']]
            c['smnAlly'] = [trait, bm.ability_value(u['passive'] or {}, capvar, lv) or 1]
        if u['name'] == 'Laviscus':
            c['outragePct'] = sm.value(ab, 'extraDmgPct', lv)
            c['chaosCrit'] = sm.value(ab, 'extraCritDmg', lv)
        if u['name'] == 'Neurothrope':
            cap = float((ab.get('constants') or {}).get('buffMaxLevel') or (ab.get('variables') or {}).get('buffMaxLevel', [15])[0])
            c['parasite'] = [sm.value(ab, 'extraDmg', lv), cap]
            if (u.get('relic') or {}).get('name') == 'Norn Crown':
                c['crown'] = sm.value(u['relic']['ability'], 'extraDmg', bm.RELIC_LEVEL, True)
        s = gr.summons_of(u, lv, g)
        if s:
            c['sum'] = [dict(n=n, d=round(dmg, 1), w=[_weapon(dict(kind=k, type=bm.dtype(w['damageProfile']), hits=w['hits'],
                                                                   pierce=w['piercingRatio'] / 100, range=1))
                                                     for k, w in (('melee', npc.get('meleeWeapon')),
                                                                  ('ranged', npc.get('rangeWeapon'))) if w],
                             src=kind)
                        for n, npc, dmg, kind in s]
        out.append(c)
    return out


def support_rows(U, lv, trig):
    """the buff each character hands the rest of the team, with its numbers worked out"""
    lookup = {u['name']: u for u in U}
    out = []
    for r in sm.load_rows('Attack'):
        if r['Name'] not in lookup:
            continue
        if r['Source'] == 'Relic' and not gr.relic_live(lookup[r['Name']], r, SETTING[4]):
            continue                      # nobody is carrying it at this setting
        ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(lookup, r)
        toks = []
        for t in sm.tokens_for(r, None, ab, relic, lv, trig):   # who it helps travels with the token
            tok = dict(k=t['kind'], s=t['scope'], o=t.get('opts') or {},
                       # per token, not per row: one ability can buff the others and the caster too
                       self=bool(gr.helps_itself(r, t['kind'])))
            if t.get('value') is not None:
                tok['v'] = round(t['value'], 2)
            if t.get('part'):
                tok['p'] = _part(t['part'])
            if t.get('cap') is not None:
                tok['cap'] = round(t['cap'], 1)
            toks.append(tok)
        if not toks:
            continue
        out.append(dict(n=r['Name'], src=r['Source'], ab=r['Ability'], rec=r['Receives'], reach=r['Reach'],
                        rel=r['Ability'] if r['Source'] == 'Relic' else None,
                        up=gr.buff_turns(r, ab), cond=r['Condition'], self=bool(gr.helps_itself(r)),
                        # kinds the caster already gets from its own ability file, so they aren't doubled
                        own=sorted(gr.own_side_kinds().get((r['Name'], r['Ability']), ())) or None, t=toks))
    return out


def vectors(g, fights, U, sp, rows, lv, trig, act, gear, tier_key, seed=11):
    """exact scores for random fives, so the page can prove it agrees with the model"""
    rnd = random.Random(seed)
    names = [u['name'] for u in U]
    by = {u['name']: u for u in U}
    out = []
    for i in range(N_VECTORS):
        fi = rnd.randrange(len(fights))
        fight = fights[fi]
        banned = gr.FACTION_ID.get(fight['faction'], fight['faction'])
        pool = [n for n in names if by[n]['faction'] != banned]
        five = rnd.sample(pool, gr.TEAM)
        dbf, high = rnd.random() < 0.5, rnd.random() < 0.5
        boss, ds, d2 = gr.boss_defender(g, fight, dbf)
        rules = gr.boss_rules(g, fight, d2 if dbf else None)
        team = [by[n] for n in five]
        opts = gr.mow_options(g, fight, boss, ds, lv, tier_key, banned, trig)
        mow = (gr.best_mow(team, opts, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None)
               if opts else None)
        got = gr.team_damage(team, boss, ds, rows, sp, lv, trig, act, gear, rules, tier_key, None, mow, high)
        out.append(dict(f=fi, d=int(dbf), h=int(high), t=five, s=round(got)))
    return out


def bosses(g, fights, lv):
    """each fight twice: as it stands, and with the side battles cleared. Each carries what every
    Machine of War you may bring does to that boss on its own, which is how the page picks one."""
    ms = list(gr.machines(g))
    out = []
    for f in fights:
        both = []
        banned = gr.FACTION_ID.get(f['faction'], f['faction'])
        for dbf in (False, True):
            boss, ds, d2 = gr.boss_defender(g, f, dbf)
            rules = gr.boss_rules(g, f, d2 if dbf else None)
            both.append(dict(arm=round(boss['arm'], 1), bc=round(ds['bc'], 3), bd=round(ds['bd'], 1),
                             ccr=round(ds['ccr'], 3), cdr=round(ds['cdr'], 1),
                             tr=sorted(boss['traits']), hp=f['hp'], ban=banned,
                             dim=list(rules['diminish']) if rules['diminish'] else None,
                             psy=rules['psyker_pct'], ramp=rules['block_ramp'],
                             dmg=round(boss['dmg'], 1),
                             mow={m['name']: round(gr.mow_damage(g, m, boss, ds, lv))
                                  for m in ms
                                  if gr.FACTION_ID.get(m['factionId'], m['factionId']) != banned}))
        out.append(both)
    return out


def build(g, fights):
    """everything the Calculate button needs, for the setting the videos use"""
    tier_key, lv, trig, act, gear = SETTING
    U, sp, _, _ = gr.setting(tier_key, lv, trig, act, gear)
    rows = sm.load_rows('Attack')
    machines = []
    for m in gr.machines(g):
        b = gr.mow_buff(g, m, lv, tier_key, trig)
        machines.append(dict(n=m['name'], f=m['factionId'],
                             b=(dict(k=b['kind'], pct=b['pct'], only=b['only'] or '', who=b['who']) if b else None)))
    return dict(version=g['version'], fingerprint=fingerprint(g), setting=dict(tier=tier_key, lv=lv, trig=trig, act=act, gear=gear),
                turns=gr.FIGHTING, adjacent=gr.ADJACENT_ALLIES, high=dict(n=gr.HIGH_GROUND, pct=gr.HIGH_GROUND_PCT),
                chars=characters(U, sp, g, lv, trig), rows=support_rows(U, lv, trig), mows=machines,
                bosses=bosses(g, fights, lv),
                vec=vectors(g, fights, U, sp, rows, lv, trig, act, gear, tier_key))
