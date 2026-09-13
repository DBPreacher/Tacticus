"""
build_typical.py - the "what does a typical character mean?" graphic for videos.

For one setting (Diamond III, always-on traits, the lower ability level, active off, no gear: the map's
opening view), works out every single matchup with build_map.py's model and writes typical-character.html:
one character's 117 answers as bars, which line up from quickest to slowest and pick out the middle one.
Its Damage (they attack everyone) and Toughness (everyone attacks them) are those middle answers, the same
numbers as on the map. Any character can be picked on the page; it opens on Kharn.

    python -X utf8 build_typical.py
"""
import json, os, statistics as st, sys
import build_map as bm

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'typical_template.html')
OUT = os.path.join(HERE, 'typical-character.html')


def main():
    bm.set_tier(bm.TIERS[1])                                   # Diamond III
    g, units = bm.load()
    actives = bm.sync_rows(bm.ACTIVES_CSV, bm.ACTIVE_COLS, 'Active', units, bm.draft_active, 'active_abilities.csv')
    passives = bm.sync_rows(bm.PASSIVES_CSV, bm.PASSIVE_COLS, 'Passive', units, bm.draft_passive, 'passive_abilities.csv')
    relics = bm.sync_relics(g, units)
    specs = bm.build_specs(units, actives, passives, relics)
    key, trig, lv, act, gear = next(k for k in bm.scenario_keys() if k[0] == bm.STANDARD)
    sp = specs[(lv, trig, gear)]
    # the same per-scenario setup as build_map.run_scenarios (no gear, active off)
    U = [dict(u, g=None) for u in units]
    for u in U:
        u['ps'] = sp['passive'].get(u['name'])
        u['pg'] = sp['passive_goff'].get(u['name'])
    rest = {u['name']: bm.merge_defence(sp['passive_def'].get(u['name']), sp['passive_gdef'].get(u['name'])) for u in U}
    K = [[round(bm.attacks_to_kill(a, d, trig, None, rest[d['name']], rest[d['name']])[0], 2) for d in U] for a in U]

    names = [u['name'] for u in U]
    i = names.index('Kharn')
    print(f'Check against the map ({key}): Kharn damage {st.median(K[i]):.2f}, toughness {st.median(r[i] for r in K):.2f} attacks')

    data = dict(version=g['version'], setting=f"Diamond III · always-on traits · abilities {lv} · active off · no gear",
                chars=[dict(n=u['name'], a=u['alliance'], f=u['faction']) for u in U], k=K, start='Kharn')
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    if '/*DATA*/' not in html:
        sys.exit('typical_template.html is missing its /*DATA*/ placeholder.')
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html.replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))
    print(f'Built typical-character.html: {len(U)} characters, game version {g["version"]}.')


if __name__ == '__main__':
    main()
