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
import random
import support_model as sm
import guild_raid as gr

SETTING = ('mythic', 60, True, True, True)     # tier, ability level, traits, actives, gear
N_VECTORS = 50                                 # exact scores the page checks itself against


def _weapon(w):
    return dict(k=w['kind'], t=w['type'], h=w['hits'], p=w['pierce'])


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


def characters(U, sp, g, lv):
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
        if spec and spec.get('parts'):
            c['sp'] = dict(p=[_part(p) for p in spec['parts']], same=bool(spec.get('same_turn')))
        if (u.get('relic') or {}).get('name'):
            c['rel'] = u['relic']['name']
        act = ((u.get('ability') or {}).get('constants') or {}).get('cooldownTurns')
        if act not in (None, ''):
            c['cd'] = int(float(act))
        s = gr.summons_of(g, u, lv)
        if s:
            c['sum'] = [dict(n=n, d=round(dmg, 1), w=[_weapon(dict(kind=k, type=w['damageProfile'], hits=w['hits'],
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
    any_ally = next(iter(U))
    out = []
    for r in sm.load_rows('Attack'):
        if r['Name'] not in lookup:
            continue
        ab, relic = (None, False) if r['Source'] == 'Trait' else sm.row_ability(lookup, r)
        toks = []
        for t in sm.tokens_for(r, any_ally, ab, relic, lv, trig):
            tok = dict(k=t['kind'], s=t['scope'], o=t.get('opts') or {})
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
                        up=gr.buff_turns(r, ab), cond=r['Condition'], self=bool(gr.helps_itself(r)), t=toks))
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
    return dict(setting=dict(tier=tier_key, lv=lv, trig=trig, act=act, gear=gear),
                turns=gr.FIGHTING, high=dict(n=gr.HIGH_GROUND, pct=gr.HIGH_GROUND_PCT),
                chars=characters(U, sp, g, lv), rows=support_rows(U, lv, trig), mows=machines,
                vec=vectors(g, fights, U, sp, rows, lv, trig, act, gear, tier_key))
