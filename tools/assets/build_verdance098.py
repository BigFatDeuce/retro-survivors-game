"""0.98 (announcements closer to Dofus Unity's lettering): the announcement font game/assets/fonts/verdance.woff2 from
Verdance Bold (its source: raw/fonts/verdance/Verdance-Bold.ttf). The font has only the 71 basic ASCII characters: this
adds what the 7 game languages need, built from its own glyphs and from marks drawn in its angular style (slanted
parallelograms like its dots): the accented letters (base + acute, grave, circumflex, diaeresis, tilde, cedilla; i
without its dot under a mark), ß as 'ss', Œ / œ as O+E / o+e, ’ ‘ “ ” „ " « » … – — · ¡ ¿ % + × = / ; ( ) ° and the
no-break spaces. Anything else (emoji, arrows) falls back to the next font of juice.js ANN_FONT. ~20 KB.
usage: python tools/assets/build_verdance098.py [Verdance-Bold.ttf] [--sample <png>]   (--sample: a picture of every added glyph)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen

SRC = f'{ROOT}/raw/fonts/verdance/Verdance-Bold.ttf'
OUT = f'{ROOT}/game/assets/fonts/verdance.woff2'
XH, CAP, GAP = 575, 700, 70   # x-height, cap height (OS/2), the gap between a letter and its mark

MARKS = {   # (unicode -> base, mark) for the accented letters
    'acute': 'áéíóúÁÉÍÓÚ', 'grave': 'àèìòùÀÈÌÒÙ', 'circ': 'âêîôûÂÊÎÔÛ', 'diaer': 'äëïöüÿÄËÏÖÜ', 'tilde': 'ãñõÃÑÕ', 'cedilla': 'çÇ'}
BASE = dict(zip('áéíóúàèìòùâêîôûäëïöüÿãñõç', 'aeiouaeiouaeiouaeiouyanoc'))


def area(pts): return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def poly(pen, pts, dx=0, dy=0):
    """One closed contour, turned clockwise (TrueType's outer contours, like the font's own)."""
    pts = [(x + dx, y + dy) for x, y in pts]
    if area(pts) > 0: pts = pts[::-1]
    pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()


def mark(pen, kind, cx, b):
    """A mark centred on cx, its foot at height b (above the letter); the dots are the font's own (158 x 176, slant 18)."""
    dot = lambda x, y, s=1: poly(pen, [(x, y + 150 * s), (x + 140 * s, y + 150 * s), (x + 156 * s, y), (x + 16 * s, y)])
    if kind == 'acute': poly(pen, [(cx - 80, b), (cx + 30, b), (cx + 150, b + 165), (cx + 40, b + 165)])
    elif kind == 'grave': poly(pen, [(cx - 30, b), (cx + 80, b), (cx - 40, b + 165), (cx - 150, b + 165)])
    elif kind == 'circ': poly(pen, [(cx - 200, b), (cx - 75, b), (cx, b + 80), (cx + 75, b), (cx + 200, b), (cx + 45, b + 170), (cx - 45, b + 170)])
    elif kind == 'diaer': dot(cx - 175, b); dot(cx + 35, b)
    elif kind == 'tilde': poly(pen, [(cx - 210, b + 10), (cx - 100, b + 130), (cx + 40, b + 70), (cx + 120, b + 150), (cx + 210, b + 150), (cx + 210, b + 80), (cx + 100, b + 10), (cx - 40, b + 70), (cx - 110, b + 10)])
    elif kind == 'cedilla': poly(pen, [(cx - 40, b), (cx + 60, b), (cx + 20, b - 120), (cx - 110, b - 200), (cx - 150, b - 160), (cx - 50, b - 100)])


def build(src=SRC):
    f = TTFont(src); gs = f.getGlyphSet(); cmap = f.getBestCmap(); glyf = f['glyf']; hmtx = f['hmtx']; order = f.getGlyphOrder()
    name = {chr(u): n for u, n in cmap.items()}
    bounds = lambda n: (lambda p: (gs[n].draw(p), p.bounds)[1])(BoundsPen(gs))
    new = {}

    def add(u, gname, draw, adv):
        pen = TTGlyphPen(None); draw(pen); new[u] = (gname, pen.glyph(), adv)

    def put(pen, n, dx=0, dy=0, m=(1, 0, 0, 1)): gs[n].draw(TransformPen(pen, (m[0], m[1], m[2], m[3], dx, dy)))
    # dotless i: the i's stem alone (its lowest contour)
    rec = RecordingPen(); gs['i'].draw(rec); stem = []
    for op, a in rec.value:
        stem.append((op, a))
        if op == 'closePath': break
    add(0x131, 'dotlessi', lambda p: [getattr(p, op)(*a) for op, a in stem], hmtx['i'][0])
    _g = {}

    def base_draw(ch):
        if ch == 'i': return lambda p: [getattr(p, op)(*a) for op, a in stem], 'i'
        return (lambda p: put(p, name[ch])), ch
    for kind, chars in MARKS.items():
        for ch in chars:
            lo = ch.islower(); bch = BASE[ch.lower()]; b = bch.upper() if not lo else bch
            draw, bn = base_draw(b); n = name[bn]; x0, y0, x1, y1 = bounds(n); cx = (x0 + x1) / 2
            top = max(XH if lo else CAP, y1 if bn != 'i' else XH) + GAP
            add(ord(ch), f'uni{ord(ch):04X}', lambda p, draw=draw, kind=kind, cx=cx, top=top: (draw(p), mark(p, kind, cx, 0 if kind == 'cedilla' else top)), hmtx[n][0])
    # ß = ss, Œ œ = O+E / o+e (the second letter over the first's right side)
    s = name['s']; add(0xDF, 'germandbls', lambda p: (put(p, s), put(p, s, hmtx[s][0] - 40)), hmtx[s][0] * 2 - 40)
    for u, a, e in ((0x152, 'O', 'E'), (0x153, 'o', 'e')):
        A, E = name[a], name[e]; sh = hmtx[A][0] - 150
        add(u, f'uni{u:04X}', lambda p, A=A, E=E, sh=sh: (put(p, A), put(p, E, sh)), sh + hmtx[E][0])
    # punctuation
    q, per, hy, qm, ex = name["'"], name['.'], name['-'], name['?'], name['!']
    for u in (0x2019, 0x2018): add(u, f'uni{u:04X}', lambda p: put(p, q), hmtx[q][0])
    for u, dy in ((0x201C, 0), (0x201D, 0), (0x22, 0), (0x201E, -620)):
        add(u, f'uni{u:04X}', lambda p, dy=dy: (put(p, q, 0, dy), put(p, q, 150, dy)), hmtx[q][0] + 150)
    chev = lambda p, x, d: poly(p, [(x, 470), (x + 110 * d, 470), (x + 260 * d, 270), (x + 110 * d, 70), (x, 70), (x + 150 * d, 270)])   # (a chevron as tall as the x-height)
    add(0xAB, 'guillemotleft', lambda p: (chev(p, 320, -1), chev(p, 510, -1)), 600)
    add(0xBB, 'guillemotright', lambda p: (chev(p, 60, 1), chev(p, 250, 1)), 600)
    add(0x2026, 'ellipsis', lambda p: [put(p, per, i * 250) for i in range(3)], 250 * 2 + hmtx[per][0])
    add(0x2013, 'endash', lambda p: put(p, hy), hmtx[hy][0])
    add(0x2014, 'emdash', lambda p: put(p, hy, -30, 0, (1.6, 0, 0, 1)), int(hmtx[hy][0] * 1.6))
    add(0xB7, 'periodcentered', lambda p: put(p, per, 0, 250), hmtx[per][0])
    for u, n, w in ((0xA1, ex, hmtx[ex][0]), (0xBF, qm, hmtx[qm][0])):   # ¡ ¿: turned over, hanging below the line
        x0, y0, x1, y1 = bounds(n); add(u, f'uni{u:04X}', lambda p, n=n, x0=x0, x1=x1, y1=y1: put(p, n, x0 + x1, y1 - 220, (-1, 0, 0, -1)), w)
    bar = lambda p, x0, y0, x1, y1: poly(p, [(x0 + 12, y1), (x1 + 12, y1), (x1, y0), (x0, y0)])
    add(0x2B, 'plus', lambda p: (bar(p, 60, 240, 500, 360), bar(p, 220, 80, 340, 240), bar(p, 220, 360, 340, 520)), 560)
    add(0x3D, 'equal', lambda p: (bar(p, 60, 140, 500, 250), bar(p, 60, 350, 500, 460)), 560)
    add(0xD7, 'multiply', lambda p: (poly(p, [(90, 90), (175, 90), (470, 430), (385, 430)]), poly(p, [(385, 90), (470, 90), (175, 430), (90, 430)])), 560)
    sl = lambda p, x: poly(p, [(x, -40), (x + 120, -40), (x + 430, 740), (x + 310, 740)])
    add(0x2F, 'slash', lambda p: sl(p, 30), 500)
    o = name['o']; small = (0.42, 0, 0, 0.42)
    add(0x25, 'percent', lambda p: (put(p, o, 30, 430, small), sl(p, 170), put(p, o, 410, 0, small)), 720)
    add(0xB0, 'degree', lambda p: put(p, o, 40, 470, small), 360)
    add(0x3B, 'semicolon', lambda p: (put(p, per, 0, 330), put(p, name[','], 0, 0)), hmtx[per][0])
    add(0x28, 'parenleft', lambda p: poly(p, [(250, 760), (370, 760), (200, 330), (370, -100), (250, -100), (70, 330)]), 400)
    add(0x29, 'parenright', lambda p: poly(p, [(30, 760), (150, 760), (330, 330), (150, -100), (30, -100), (200, 330)]), 400)
    # write: new glyphs, the cmap, the no-break spaces as spaces
    for u, (gname, g, adv) in new.items():
        if gname not in glyf.glyphs: order.append(gname)
        glyf.glyphs[gname] = g; g.recalcBounds(glyf); hmtx.metrics[gname] = (int(adv), int(getattr(g, 'xMin', 0) or 0))
    f.setGlyphOrder(order); f['maxp'].numGlyphs = len(order)
    sp = name[' ']
    for t in f['cmap'].tables:
        if t.isUnicode():
            for u, (gname, _, _) in new.items(): t.cmap[u] = gname
            for u in (0xA0, 0x202F, 0x2009): t.cmap[u] = sp
    f['post'].formatType = 3.0   # (no glyph names to store)
    return f, sorted(new)


if __name__ == '__main__':
    args = sys.argv[1:]; sample = None
    if '--sample' in args: i = args.index('--sample'); sample = args[i + 1]; del args[i:i + 2]
    f, added = build(args[0] if args else SRC)
    f.flavor = 'woff2'; f.save(OUT)
    print(OUT, len(f.getGlyphOrder()), 'glyphs,', len(added), 'added:', ''.join(chr(u) for u in added))
    if sample:   # every added glyph next to its plain letters, big
        import io
        from PIL import Image, ImageDraw, ImageFont
        f.flavor = None; b = io.BytesIO(); f.save(b); b.seek(0)
        fnt = ImageFont.truetype(b, 72); im = Image.new('RGB', (1800, 560), (34, 52, 44)); g = ImageDraw.Draw(im)
        lines = ['àâäéèêëîïôöùûüç ÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ', 'áíóúñãõ ÁÍÓÚÑÃÕ ß Œœ ¡¿', '« Victoire ! » “GO” „x” l’été… — – · % + × = / ; (a) 3°',
                 'Défaite — Bouftou Royal apparaît !']
        for i, s in enumerate(lines): g.text((20, 20 + i * 130), s, font=fnt, fill=(240, 235, 220))
        im.save(sample); print('sample', sample)
