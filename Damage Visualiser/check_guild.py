"""
check_guild.py - score the real runs the owner has found, so a change to the model can be checked in
seconds instead of waiting half an hour for a page build.

    python -X utf8 check_guild.py

Each row is a team someone actually played in a video, with the damage they did. The model should land
near it. If a change swings one of these, that is the change to look at.
See INSTRUCTIONS.md ("Guild Raid", Calibration).
"""
import support_model as sm
import guild_raid as gr

# boss, level, the five, what the video shows, where it came from
RUNS = [
    ('Mortarion', 25, ['Laviscus', 'Atlacoya', 'Boss Gulgortz', 'Trajann', 'Kariyan'], 1_632_137,
     'Mythic 3, a short from early September 2026'),
    ('Mortarion', 25, ['Laviscus', 'Atlacoya', 'Boss Gulgortz', 'Trajann', 'Kariyan'], 1_660_000,
     'Mythic 3, a second short of the same five'),
    ('Szarekh', 24, ['Aesoth', 'Boss Gulgortz', 'Trajann', 'Laviscus', 'Kariyan'], 2_620_000,
     'Mythic 2, before Mythic 3 existed'),
]
TIER, LEVEL, GEAR, TRIG, ACT, DEBUFFS, HIGH = 'mythic', 60, True, True, True, True, True


def main():
    g = gr.game()
    rows = sm.load_rows('Attack')
    U, sp, _, _ = gr.setting(TIER, LEVEL, TRIG, ACT, GEAR)
    by = {u['name']: u for u in U}
    print(f'{TIER}, abilities {LEVEL}, {"gear" if GEAR else "no gear"}, '
          f'{"all triggered" if TRIG else "always-on"}, side battles '
          f'{"cleared" if DEBUFFS else "not cleared"}, {"high ground" if HIGH else "no high ground"}\n')
    worst = 0.0
    for name, lvl, five, real, note in RUNS:
        fight = [f for f in gr.fights(g) if f['name'].startswith(name) and f['level'] == lvl][0]
        boss, ds, dbf = gr.boss_defender(g, fight, DEBUFFS)
        rules = gr.boss_rules(g, fight, dbf if DEBUFFS else None)
        banned = gr.FACTION_ID.get(fight['faction'], fight['faction'])
        team = [by[n] for n in five]
        opts = gr.mow_options(g, fight, boss, ds, LEVEL, TIER, banned, TRIG)
        mow = gr.best_mow(team, opts, boss, ds, rows, sp, LEVEL, TRIG, ACT, GEAR, rules, TIER, None) if opts else None
        got = gr.team_damage(team, boss, ds, rows, sp, LEVEL, TRIG, ACT, GEAR, rules, TIER, None, mow, HIGH)
        off = got / real - 1
        worst = max(worst, abs(off))
        print(f'{name} L{lvl:<3} {", ".join(x[:9] for x in five):<52} real {real:>10,}  model {got:>10,.0f}  '
              f'{off:+6.1%}   {mow["name"] if mow else "no machine"}')
        print(f'{"":>14}{note}')
    print(f'\nWorst miss: {worst:.1%}')


if __name__ == '__main__':
    main()
