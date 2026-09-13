#!/usr/bin/env python3
"""
Tacticus character database audit against tacticus.wiki.gg

Checks every character in tacticus_characters.csv against its wiki.gg page and
reports:
  1. Changelog entries dated on/after --since (default: July 2026) - i.e. every
     rework/buff/trait change the wiki has recorded since the last full pass.
  2. Mismatches between the wiki's stat box and the CSV: traits, hit counts,
     primary melee/ranged damage types, Has_Ranged.

It only reports - it never edits the CSV. Mismatches still need a human check
(the wiki itself is sometimes wrong or behind - cross-check tacticustable.com).
Ability-text-derived columns (Has_[DamageType] from abilities, Self_Heal,
Shielding, Spawner) can't be checked automatically - for anyone with a recent
changelog entry, re-read their abilities by hand.

Usage:
    python -X utf8 wiki_audit.py [--csv tacticus_characters.csv] [--since "July 2026"]
"""

import argparse, csv, json, re, sys, time, unicodedata, urllib.parse, urllib.request

API = 'https://tacticus.wiki.gg/api.php'
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july',
          'august', 'september', 'october', 'november', 'december']
# Wiki spelling -> CSV spelling, for damage types that differ
DAMAGE_ALIASES = {'eviscerate': 'Eviscerating', 'gauss': 'Molecular'}
# Wiki traits that exist but aren't tracked as CSV columns
IGNORED_TRAITS = {'summon', 'none'}
# CSV values the owner has confirmed where the wiki is wrong - not reported.
# Remove an entry if the wiki is later corrected.
CONFIRMED = {
    ('Uthar', 'Ranged_Hits'): 'owner confirmed 4 in-game (Sept 2026); wiki says 2',
    ('Uthar', 'X_Hits_Restriction'): 'follows Ranged_Hits',
}


def api_get(params):
    params = dict(params, format='json', formatversion='2')
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'TacticusLEPlanner-audit/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)


def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r"[^a-z0-9 ]", '', s.lower().replace('-', ' ').replace('_', ' ')).strip()


def wiki_character_titles():
    titles = []
    for category in ('Category:Characters', 'Category:MoW'):
        cont = {}
        while True:
            data = api_get({'action': 'query', 'list': 'categorymembers',
                            'cmtitle': category, 'cmlimit': '500', **cont})
            titles += [m['title'] for m in data['query']['categorymembers']]
            if 'continue' not in data:
                break
            cont = data['continue']
    return sorted(set(titles))


def match_title(name, titles):
    n = norm(name)
    by_norm = {norm(t): t for t in titles}
    if n in by_norm:
        return by_norm[n]
    # CSV often uses the short name ("Uthar" -> "Uthar the Destined")
    starts = [t for k, t in by_norm.items() if k.startswith(n + ' ') or n.startswith(k + ' ')]
    return starts[0] if len(starts) == 1 else None


def fetch_wikitext(titles):
    out = {}
    for i in range(0, len(titles), 50):
        data = api_get({'action': 'query', 'prop': 'revisions', 'rvprop': 'content',
                        'rvslots': 'main', 'titles': '|'.join(titles[i:i + 50])})
        for p in data['query']['pages']:
            if 'revisions' in p:
                out[p['title']] = p['revisions'][0]['slots']['main']['content']
    return out


def infobox_field(text, field):
    m = re.search(r'\|\s*' + field + r'\s*=([^|}]*)', text)
    return m.group(1).strip() if m else None


def parse_attack(value):
    """'[[Energy]] / 4 hits / Range 2' -> ('Energy', 4)"""
    if not value:
        return None, None
    dtype = re.search(r'\[\[([^\]|]+)', value)
    hits = re.search(r'(\d+)\s*hits?', value)
    d = dtype.group(1).strip() if dtype else None
    if d:
        d = DAMAGE_ALIASES.get(d.lower(), d)
    return d, int(hits.group(1)) if hits else None


def parse_traits(value):
    if not value:
        return set()
    return {t.strip() for t in re.findall(r'\[\[([^\]|]+)', value)}


def changelog_since(text, since_year, since_month):
    m = re.search(r'==\s*Changelog\s*==(.*?)(?:\n==[^=]|\{\{CharNav|\Z)', text, re.S | re.I)
    if not m:
        return []
    entries = []
    for line in m.group(1).splitlines():
        d = re.match(r'\s*\*?\s*([A-Za-z]+)\s+(\d{4})\s*:\s*(.*)', line)
        if not d or d.group(1).lower() not in MONTHS:
            continue
        month, year = MONTHS.index(d.group(1).lower()) + 1, int(d.group(2))
        if (year, month) >= (since_year, since_month):
            entries.append(f'{d.group(1)} {year}: {d.group(3).strip()}')
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', default='tacticus_characters.csv')
    ap.add_argument('--since', default='July 2026', help='e.g. "July 2026"')
    args = ap.parse_args()
    sm, sy = args.since.split()
    since = (int(sy), MONTHS.index(sm.lower()) + 1)

    with open(args.csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    trait_cols = header[header.index('Act_of_Faith'):header.index('Has_Bio')]
    trait_col_by_norm = {norm(c): c for c in trait_cols}

    titles = wiki_character_titles()
    mapping = {r['Name']: match_title(r['Name'], titles) for r in rows}
    pages = fetch_wikitext(sorted({t for t in mapping.values() if t}))

    # analysis = columns le_analysis.py actually filters on (traits, hits,
    # Has_Ranged, Has_[DamageType]); reference = the Melee/Ranged_Damage_Type
    # text columns, which the analysis never reads
    changed, analysis, reference, unmatched = [], [], [], []
    for r in rows:
        name, title = r['Name'], mapping[r['Name']]
        text = pages.get(title) if title else None
        if not text:
            unmatched.append(name)
            continue

        log = changelog_since(text, *since)
        if log:
            changed.append((name, title, log))

        issues, ref_issues = [], []
        wiki_traits = parse_traits(infobox_field(text, 'traits'))
        wiki_cols = set()
        for t in wiki_traits:
            col = trait_col_by_norm.get(norm(t))
            if col:
                wiki_cols.add(col)
            elif norm(t) not in IGNORED_TRAITS:
                issues.append(f'wiki trait "{t}" has no CSV column')
        csv_cols = {c for c in trait_cols if r[c] == 'Y'}
        for c in sorted(wiki_cols - csv_cols):
            issues.append(f'{c}: wiki has it, CSV says N')
        for c in sorted(csv_cols - wiki_cols):
            issues.append(f'{c}: CSV says Y, not on wiki')

        m_type, m_hits = parse_attack(infobox_field(text, 'melee_attack'))
        r_type, r_hits = parse_attack(infobox_field(text, 'ranged_attack'))
        is_mow = r['Is_MoW'] == 'Y'

        def differs(wiki_val, csv_val, col=None):
            if (name, col) in CONFIRMED:
                return False
            if is_mow and not wiki_val:
                return False  # MoW stat blocks are often blank on purpose
            return str(wiki_val or '').lower() != str(csv_val or '').lower()

        wiki_has_ranged = 'Y' if r_type or r_hits else ('N' if m_type or not is_mow else None)
        for col, wiki_val in [('Melee_Hits', m_hits), ('Ranged_Hits', r_hits),
                              ('Has_Ranged', wiki_has_ranged)]:
            if differs(wiki_val, r[col], col):
                issues.append(f'{col}: wiki={wiki_val or "(blank)"}  CSV={r[col] or "(blank)"}')
        wiki_x = r_hits if r_hits else m_hits
        if differs(wiki_x, r['X_Hits_Restriction'], 'X_Hits_Restriction'):
            issues.append(f'X_Hits_Restriction: wiki implies {wiki_x}  CSV={r["X_Hits_Restriction"] or "(blank)"}')
        for kind, wiki_type in [('melee', m_type), ('ranged', r_type)]:
            col = 'Has_' + (wiki_type or '').replace(' ', '_')
            if wiki_type and col in r and r[col] != 'Y':
                issues.append(f'{col}: wiki {kind} attack is {wiki_type}, CSV says N')

        for col, wiki_val in [('Melee_Damage_Type', m_type), ('Ranged_Damage_Type', r_type)]:
            if differs(wiki_val, r[col]):
                ref_issues.append(f'{col.split("_")[0]} wiki={wiki_val or "-"}/CSV={r[col] or "-"}')
        if issues:
            analysis.append((name, title, issues))
        if ref_issues:
            reference.append((name, ref_issues))

    print(f'Tacticus wiki audit - {len(rows)} CSV rows, changelog cutoff {args.since}\n')
    print(f'=== 1. Wiki changelog entries since {args.since} ({len(changed)} characters) ===')
    print('    Re-read these characters\' abilities too - Has_[DamageType], Self_Heal,')
    print('    Shielding and Spawner can change with a rework and aren\'t checked below.\n')
    for name, title, log in changed:
        print(f'  {name}' + (f'  [{title}]' if title != name else ''))
        for e in log:
            print(f'      {e}')
    print(f'\n=== 2. Mismatches that affect LE analysis ({len(analysis)} characters) ===')
    print('    Traits, hit counts, Has_Ranged, and Has_[DamageType] for the wiki\'s primary attacks.\n')
    for name, title, issues in analysis:
        print(f'  {name}' + (f'  [{title}]' if title != name else ''))
        for i in issues:
            print(f'      {i}')
    print(f'\n=== 3. Reference-only mismatches: Melee/Ranged_Damage_Type text ({len(reference)} characters) ===')
    print('    le_analysis.py never reads these columns - low priority.\n')
    for name, ref_issues in reference:
        print(f'  {name}: ' + '; '.join(ref_issues))
    if unmatched:
        print(f'\n=== No wiki page matched ({len(unmatched)}) - check by hand ===\n')
        print('  ' + ', '.join(unmatched))


if __name__ == '__main__':
    main()
