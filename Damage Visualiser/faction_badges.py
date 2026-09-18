"""
faction_badges.py - the faction icons, trimmed and squared up so they can be drawn as chart marks.

The source art is the owner's, at FACTION_BADGES below: nineteen ripped from the game at about 256px and
three taken from the wiki, in a different size and padding. A chart needs them all the same size and
optically centred, so this trims each one to its opaque pixels, scales the long edge to SIZE, and centres
it on a transparent square. Nothing is upscaled: the smallest source (Tau, 128px) still comes down.

The results go in `faction_badges/`, named for the faction, so the page build never has to reach outside
the repo. Re-run it when a new faction arrives:

    python -X utf8 faction_badges.py

It also prints each badge's signature colour - the most common strong hue in it - which is useful when a
badge needs a fallback swatch.

The saved badges are quantised to COLOURS, because the page inlines all 22 as data URIs and full RGBA
came to 262 KB of base64. At 128 colours that is 76 KB and, side by side at 64px, the two are
indistinguishable.

See PLAN.md, "Faction badges".
"""
import collections
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = r'E:\Video Production\Assets\Images\Game Renders\Faction badges'
OUT = os.path.join(HERE, 'faction_badges')
SIZE = 64                     # the long edge of a mark on the chart, at 1x
COLOURS = 128                 # palette size; see the note above about inlined weight

# The game's file names are not the faction names, and the three from the wiki follow a different
# convention again, so the mapping is written out rather than guessed.
BADGES = {
    'ui_icon_faction_adeptas_01.png': 'Adepta Sororitas',
    'ui_icon_faction_adeptus_mechanicus_01.png': 'Adeptus Mechanicus',
    'ui_icon_faction_aeldari_01.png': 'Aeldari',
    'ui_icon_faction_astra_militarum_01.png': 'Astra Militarum',
    'ui_icon_faction_black_legion_01.png': 'Black Legion',
    'ui_icon_faction_black_templars_01.png': 'Black Templars',
    'ui_icon_faction_blood_angels.png': 'Blood Angels',
    'ui_icon_faction_custodes.png': 'Adeptus Custodes',
    'ui_icon_faction_dark_angels_01.png': 'Dark Angels',
    'ui_icon_faction_death_guard_01.png': 'Death Guard',
    'ui_icon_faction_genestealers.png': 'Genestealer Cults',
    'ui_icon_faction_necron_01.png': 'Necrons',
    'ui_icon_faction_orks_01.png': 'Orks',
    'ui_icon_faction_space_wolves_01.png': 'Space Wolves',
    'ui_icon_faction_tau_01.png': 'Tau Empire',
    'ui_icon_faction_thousand_sons_01.png': 'Thousand Sons',
    'ui_icon_faction_tyranids_01.png': 'Tyranids',
    'ui_icon_faction_ultramarine_01.png': 'Ultramarines',
    'ui_icon_faction_world_eaters_01.png': 'World Eaters',
    'Adeptus_Astartes_Icon.png': 'Adeptus Astartes',
    "Emperor's_Children_Icon.png": "Emperor's Children",
    'Leagues_of_Votann_Icon.png': 'Leagues of Votann',
}


def squared(im, size=SIZE):
    """trimmed to its opaque pixels, scaled to fit, and centred on a transparent square"""
    im = im.convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        im = im.crop(box)
    w, h = im.size
    scale = size / max(w, h)
    im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    out.paste(im, ((size - im.size[0]) // 2, (size - im.size[1]) // 2), im)
    return out


def signature_colour(im):
    """the most common strong colour in the badge, for a fallback swatch. Near-black and near-white are
    skipped because most badges have plenty of both and neither identifies anyone."""
    counts = collections.Counter()
    for r, g, b, a in im.getdata():
        if a < 200:
            continue
        hi, lo = max(r, g, b), min(r, g, b)
        if hi < 60 or (hi - lo) < 40:          # too dark, or too grey to be a signature
            continue
        counts[(r // 24 * 24, g // 24 * 24, b // 24 * 24)] += 1
    if not counts:
        return '#9aa3b2'                        # a badge with no colour of its own
    r, g, b = counts.most_common(1)[0][0]
    return f'#{min(r + 12, 255):02x}{min(g + 12, 255):02x}{min(b + 12, 255):02x}'


def main():
    if not os.path.isdir(SOURCE):
        sys.exit(f'The badge art is not where it should be:\n  {SOURCE}')
    os.makedirs(OUT, exist_ok=True)
    have = set(os.listdir(SOURCE))
    missing = [f for f in BADGES if f not in have]
    if missing:
        sys.exit('Missing badge art: ' + ', '.join(missing))
    print(f"{'faction':22} {'from':>11} {'to':>9}  signature")
    for name, faction in sorted(BADGES.items(), key=lambda x: x[1]):
        im = Image.open(os.path.join(SOURCE, name))
        was = im.size
        small = squared(im)
        sig = signature_colour(small)        # read the colour before the palette flattens it
        small.quantize(colors=COLOURS, method=Image.FASTOCTREE).save(
            os.path.join(OUT, faction + '.png'), optimize=True)
        print(f'   {faction:22} {str(was):>11} {str(small.size):>9}  {sig}')
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f'\n{len(BADGES)} badges in faction_badges/, {total / 1024:.0f} KB in total '
          f'({total * 4 / 3 / 1024:.0f} KB inlined as data URIs).')


if __name__ == '__main__':
    main()
