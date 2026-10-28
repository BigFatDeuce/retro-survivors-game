"""Booster pack pictures (PNG) from tools/assets/boosters/booster.html + boosters.json.
Each pack in boosters.json may give its own "art" (the character in the middle) and "logo" (paths to transparent PNGs,
relative to the repo root); when absent, placeholder drawings are used (an original creature, a text logo).
Per pack: "colors" (c_light, c_mid, c_dark, c_accent, c_body), "pattern" (background decoration, see PATTERNS),
"rings" (false = no rings around the character), "holo" (rainbow foil under the character, 0..1) and "look" (the
placeholder creature: body, crest, eyes, mouth — see BODIES, CRESTS, EYES, MOUTHS; the old "crest" key still works).
Usage: python tools/assets/boosters/build_boosters.py [ids…]   -> dist/boosters/<id>.png (1400×2200, transparent)"""
import os, sys, json, math, random, base64
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # (tools/assets/boosters -> the repository)
OUT = os.path.join(ROOT, 'dist', 'boosters')
LINE = '#3b1d07'   # outline colour of the drawings


def pack_shape():
    """the pack outline: crimped (zigzag) top and bottom, slightly pinched sides"""
    n, tw, th = 24, 600 / 24, 20
    top = ' '.join(f'L{i * tw + tw / 2:.1f},0 L{(i + 1) * tw:.1f},{th}' for i in range(n))
    bot = ' '.join(f'L{600 - (i * tw + tw / 2):.1f},1000 L{600 - (i + 1) * tw:.1f},{1000 - th}' for i in range(n))
    return (f'M0,{th} {top} C606,250 606,750 600,{1000 - th} {bot} C-6,750 -6,250 0,{th} Z')


def img_tag(path, cls=''):
    p = os.path.join(ROOT, path)
    data = base64.b64encode(open(p, 'rb').read()).decode()
    return f'<img class="{cls}" src="data:image/png;base64,{data}">'


# ---------------------------------------------------------------- background patterns (600 × 1000 pack coordinates)
def _mask():
    """radial mask: calm in the middle (where the character stands), the pattern shows towards the edges"""
    return ('<radialGradient id="emg" cx="300" cy="490" r="560" gradientUnits="userSpaceOnUse">'
            '<stop offset=".22" stop-color="#000"/><stop offset=".78" stop-color="#fff"/></radialGradient>'
            '<mask id="em" maskUnits="userSpaceOnUse" x="0" y="0" width="600" height="1000">'
            '<rect width="600" height="1000" fill="url(#emg)"/></mask>')


def _svg(inner, defs='', masked=True):
    g = f'<g mask="url(#em)">{inner}</g>' if masked else inner
    return f'<svg class="pat" width="600" height="1000" viewBox="0 0 600 1000"><defs>{_mask() if masked else ""}{defs}</defs>{g}</svg>'


def _pts(pts):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)


def star4(x, y, s, col='#fff', op=1.0):
    return (f'<path d="M{x:.1f},{y - s:.1f} Q{x:.1f},{y:.1f} {x + s:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y + s:.1f} '
            f'Q{x:.1f},{y:.1f} {x - s:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y - s:.1f}Z" fill="{col}" opacity="{op:.2f}"/>')


def p_rays(c, rnd):
    return '<div class="rays"></div>'


def p_hex(c, rnd):
    r = 30; w = math.sqrt(3) * r; out = []
    for row in range(-1, int(1000 / (1.5 * r)) + 2):
        for col in range(-1, int(600 / w) + 2):
            cx = col * w + (w / 2 if row % 2 else 0); cy = row * 1.5 * r
            pts = [(cx + (r - 3) * math.cos(math.radians(60 * k + 30)), cy + (r - 3) * math.sin(math.radians(60 * k + 30))) for k in range(6)]
            fill = 'rgba(255,255,255,.16)' if rnd.random() < .14 else 'none'
            out.append(f'<polygon points="{_pts(pts)}" fill="{fill}" stroke="rgba(255,255,255,.32)" stroke-width="3"/>')
    return _svg(''.join(out))


def p_stars(c, rnd):
    defs = (f'<radialGradient id="n1"><stop offset="0" stop-color="{c["c_accent"]}" stop-opacity=".5"/><stop offset="1" stop-color="{c["c_accent"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="n2"><stop offset="0" stop-color="{c["c_light"]}" stop-opacity=".45"/><stop offset="1" stop-color="{c["c_light"]}" stop-opacity="0"/></radialGradient>')
    out = ['<ellipse cx="110" cy="320" rx="270" ry="210" fill="url(#n1)"/>', '<ellipse cx="490" cy="760" rx="290" ry="230" fill="url(#n2)"/>',
           '<ellipse cx="520" cy="230" rx="170" ry="130" fill="url(#n2)"/>', '<ellipse cx="90" cy="840" rx="160" ry="120" fill="url(#n1)"/>']
    for _ in range(190):
        x, y, r = rnd.uniform(0, 600), rnd.uniform(0, 1000), rnd.choice([.8, 1, 1.2, 1.6, 2.2, 2.8])
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{rnd.uniform(.35, 1):.2f}"/>')
    for _ in range(10):
        out.append(star4(rnd.uniform(30, 570), rnd.uniform(130, 880), rnd.uniform(7, 15), '#fff', .95))
    # a ringed planet and a comet
    out.append(f'<circle cx="505" cy="330" r="34" fill="{c["c_accent"]}" opacity=".85"/><circle cx="495" cy="320" r="34" fill="{c["c_dark"]}" opacity=".35"/>'
               f'<ellipse cx="505" cy="330" rx="62" ry="13" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="4" transform="rotate(-20 505 330)"/>')
    out.append('<path d="M70 200 L170 150" stroke="#fff" stroke-opacity=".45" stroke-width="5" stroke-linecap="round"/><circle cx="172" cy="149" r="6" fill="#fff"/>')
    return _svg(''.join(out), defs, masked=False)


def p_swirl(c, rnd):
    cx, cy, n, out = 300, 480, 16, []
    for i in range(n):
        a0 = 2 * math.pi * i / n; d = math.pi / n; p1, p2 = [], []
        for k in range(64):
            rr = 4 + k * 16; th = a0 + 1.15 * math.log(1 + rr / 60)
            p1.append((cx + rr * math.cos(th), cy + rr * math.sin(th))); p2.append((cx + rr * math.cos(th + d), cy + rr * math.sin(th + d)))
        out.append(f'<polygon points="{_pts(p1 + p2[::-1])}" fill="rgba(255,255,255,.15)"/>')
    return _svg(''.join(out), masked=False)


def p_diamonds(c, rnd):
    w, h, out = 80, 120, []
    for j in range(-1, 1000 * 2 // h + 2):
        for i in range(-1, 600 // w + 2):
            x = i * w + (w / 2 if j % 2 else 0); y = j * h / 2
            op = .15 if (i + j // 2) % 2 == 0 else .05
            out.append(f'<polygon points="{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}" fill="rgba(255,255,255,{op})"/>')
    k = 1000 * w / h
    for i in range(-16, 24):
        x0 = i * w
        out.append(f'<line x1="{x0}" y1="-60" x2="{x0 + k}" y2="940" stroke="{c["c_accent"]}" stroke-opacity=".45" stroke-width="2" stroke-dasharray="7 7"/>')
        out.append(f'<line x1="{x0}" y1="-60" x2="{x0 - k}" y2="940" stroke="{c["c_accent"]}" stroke-opacity=".45" stroke-width="2" stroke-dasharray="7 7"/>')
    return _svg(''.join(out))


def p_waves(c, rnd):
    out = []
    for k in range(24):
        y0 = -40 + k * 46; amp = 15; lam = 150; ph = k * .8
        top = ' '.join(f'L{x},{y0 + amp * math.sin(x / lam * 2 * math.pi + ph):.1f}' for x in range(0, 601, 10))
        bot = ' '.join(f'L{x},{y0 + 24 + amp * math.sin(x / lam * 2 * math.pi + ph + .7):.1f}' for x in range(600, -1, -10))
        out.append(f'<path d="M0,{y0} {top} {bot} Z" fill="rgba(255,255,255,{.16 if k % 2 else .07})"/>')
    for _ in range(30):   # foam dots
        x, y = rnd.uniform(0, 600), rnd.uniform(0, 1000)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(2, 5):.1f}" fill="#fff" opacity=".55"/>')
    return _svg(''.join(out))


def p_bubbles(c, rnd):
    out = []
    for _ in range(50):
        x, y, r = rnd.uniform(0, 600), rnd.uniform(0, 1000), rnd.choice([8, 12, 16, 22, 30, 40, 54])
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.5)" stroke-width="2.5"/>'
                   f'<path d="M{x - r * .55:.1f},{y - r * .15:.1f} A{r * .6:.1f},{r * .6:.1f} 0 0 1 {x - r * .1:.1f},{y - r * .6:.1f}" fill="none" '
                   f'stroke="#fff" stroke-opacity=".85" stroke-width="{max(1.5, r / 9):.1f}" stroke-linecap="round"/>')
    return _svg(''.join(out))


def p_halftone(c, rnd):
    out, s = [], 20
    for j in range(0, 1000 // s + 2):
        for i in range(-1, 600 // s + 2):
            x = i * s + (s / 2 if j % 2 else 0); y = j * s
            d = math.hypot(x - 300, (y - 490) * .75) / 420
            r = min(s * .5, 1 + 8.5 * d ** 1.6)
            if r > .7: out.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}"/>')
    return _svg(f'<g fill="rgba(255,255,255,.26)">{"".join(out)}</g>', masked=False)


def p_cracks(c, rnd):
    defs = '<filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="5"/></filter>'
    paths = []

    def branch(x, y, ang, length, depth):
        pts = [(x, y)]
        for _ in range(max(2, int(length / 14))):
            ang += rnd.uniform(-.45, .45); x += 14 * math.cos(ang); y += 14 * math.sin(ang); pts.append((x, y))
        paths.append((pts, depth))
        if depth < 3:
            for _ in range(rnd.randint(1, 2)):
                bx, by = pts[rnd.randrange(1, len(pts))]
                branch(bx, by, ang + rnd.choice([-1, 1]) * rnd.uniform(.5, 1.1), length * .55, depth + 1)
    for _ in range(10):
        side = rnd.randrange(4)
        x, y, a = [(rnd.uniform(0, 600), 0, math.pi / 2), (600, rnd.uniform(0, 1000), math.pi),
                   (rnd.uniform(0, 600), 1000, -math.pi / 2), (0, rnd.uniform(0, 1000), 0)][side]
        branch(x, y, a + rnd.uniform(-.5, .5), rnd.uniform(240, 400), 0)
    glow = ''.join(f'<polyline points="{_pts(p)}" stroke-width="{12 - 2.5 * d:.1f}"/>' for p, d in paths)
    core = ''.join(f'<polyline points="{_pts(p)}" stroke-width="{4 - .9 * d:.1f}"/>' for p, d in paths)
    inner = (f'<g fill="none" stroke="{c["c_accent"]}" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)">{glow}</g>'
             f'<g fill="none" stroke="#fff3c0" stroke-linecap="round" stroke-linejoin="round">{core}</g>')
    for _ in range(26):   # embers
        x, y = rnd.uniform(0, 600), rnd.uniform(0, 1000)
        inner += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(1.5, 4):.1f}" fill="{c["c_accent"]}" opacity="{rnd.uniform(.5, 1):.2f}"/>'
    return _svg(inner, defs)


def p_clouds(c, rnd):
    out = []
    blobs = [(0, 0, 40), (38, -16, 36), (74, 0, 40), (30, 18, 36), (-36, 10, 28), (108, 14, 28)]
    for _ in range(12):
        x, y, s = rnd.uniform(-40, 640), rnd.uniform(60, 960), rnd.uniform(.6, 1.4)
        g = ''.join(f'<circle cx="{x + bx * s:.0f}" cy="{y + by * s:.0f}" r="{br * s:.0f}"/>' for bx, by, br in blobs)
        out.append(f'<g fill="#fff" opacity="{rnd.uniform(.22, .4):.2f}">{g}</g>')
    return _svg(''.join(out))


def p_confetti(c, rnd):
    cols = [c['c_accent'], c['c_light'], '#ffffff', '#7af0ff', '#ffe066', '#9b7bff', '#ff8fb8']
    out = []
    for _ in range(170):
        x, y = rnd.uniform(0, 600), rnd.uniform(0, 1000); w, h = rnd.uniform(7, 15), rnd.uniform(3.5, 6)
        out.append(f'<rect x="{x - w / 2:.0f}" y="{y - h / 2:.0f}" width="{w:.0f}" height="{h:.0f}" rx="1.5" fill="{rnd.choice(cols)}" '
                   f'opacity="{rnd.uniform(.6, .95):.2f}" transform="rotate({rnd.uniform(0, 180):.0f} {x:.0f} {y:.0f})"/>')
    for _ in range(30):
        out.append(f'<circle cx="{rnd.uniform(0, 600):.0f}" cy="{rnd.uniform(0, 1000):.0f}" r="{rnd.uniform(3, 6):.1f}" fill="{rnd.choice(cols)}" opacity=".85"/>')
    for _ in range(8):   # streamers
        x, y = rnd.uniform(0, 600), rnd.uniform(0, 1000); a = rnd.uniform(0, 6.28)
        d = ' '.join(f'L{x + k * 7 * math.cos(a) + 9 * math.sin(k * .9):.1f},{y + k * 7 * math.sin(a) + 9 * math.cos(k * .9):.1f}' for k in range(1, 9))
        out.append(f'<path d="M{x:.0f},{y:.0f} {d}" fill="none" stroke="{rnd.choice(cols)}" stroke-width="3.5" stroke-linecap="round" opacity=".85"/>')
    return _svg(''.join(out))


def p_lowpoly(c, rnd):
    step = 75; cols, rows = 600 // step + 2, 1000 // step + 2
    P = [[(i * step + (rnd.uniform(-26, 26) if 0 < i < cols - 1 else 0), j * step + (rnd.uniform(-26, 26) if 0 < j < rows - 1 else 0))
          for i in range(cols)] for j in range(rows)]
    out = []
    for j in range(rows - 1):
        for i in range(cols - 1):
            a, b, cc, d = P[j][i], P[j][i + 1], P[j + 1][i + 1], P[j + 1][i]
            tris = [(a, b, cc), (a, cc, d)] if rnd.random() < .5 else [(a, b, d), (b, cc, d)]
            for t in tris:
                v = rnd.uniform(-.2, .24)
                col, op = ('#fff', v) if v > 0 else ('#000', -v)
                out.append(f'<polygon points="{_pts(t)}" fill="{col}" fill-opacity="{op:.2f}" stroke="rgba(255,255,255,.18)" stroke-width="1.2" stroke-linejoin="round"/>')
    return _svg(''.join(out), masked=False)


def p_synthgrid(c, rnd):
    hz, vx = 650, 300
    rects = ['<rect x="0" y="0" width="600" height="500"/>']
    y, gap, band = 500, 5, 26
    while y < 700:
        rects.append(f'<rect x="0" y="{y}" width="600" height="{band}"/>'); y += band + gap; band = max(6, band - 4); gap += 3
    defs = (f'<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6a8"/>'
            f'<stop offset=".55" stop-color="{c["c_accent"]}"/><stop offset="1" stop-color="{c["c_mid"]}"/></linearGradient>'
            f'<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c["c_dark"]}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{c["c_dark"]}" stop-opacity=".95"/></linearGradient>'
            '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3.5"/></filter>'
            f'<clipPath id="sunclip">{"".join(rects)}</clipPath>')
    stars = ''.join(f'<circle cx="{rnd.uniform(0, 600):.0f}" cy="{rnd.uniform(90, 600):.0f}" r="{rnd.choice([1, 1.4, 2])}" fill="#fff" opacity="{rnd.uniform(.4, 1):.2f}"/>' for _ in range(70))
    sun = f'<circle cx="300" cy="470" r="215" fill="url(#sun)" clip-path="url(#sunclip)"/>'
    lines = []
    k = 0
    while True:
        yy = hz + 5 * (1.32 ** k); k += 1
        if yy > 1000: break
        lines.append(f'<line x1="0" y1="{yy:.1f}" x2="600" y2="{yy:.1f}"/>')
    for i in range(-14, 15):
        lines.append(f'<line x1="{vx + i * 7}" y1="{hz}" x2="{vx + i * 95}" y2="1000"/>')
    grid = ''.join(lines)
    inner = (stars + sun + f'<rect x="0" y="{hz}" width="600" height="{1000 - hz}" fill="url(#floor)"/>'
             f'<g stroke="{c["c_accent"]}" stroke-width="5" opacity=".7" filter="url(#glow)">{grid}</g>'
             f'<g stroke="#ffe6fb" stroke-width="2">{grid}</g>'
             f'<line x1="0" y1="{hz}" x2="600" y2="{hz}" stroke="#fff" stroke-width="3"/>')
    return _svg(inner, defs, masked=False)


def p_burst(c, rnd):
    cx, cy, n = 300, 490, 22
    def burst(r1, r2, rot=0):
        return _pts([(cx + (r1 if k % 2 == 0 else r2) * math.cos(math.pi * k / n + rot), cy + (r1 if k % 2 == 0 else r2) * math.sin(math.pi * k / n + rot)) for k in range(2 * n)])
    lines = []
    for _ in range(70):
        a = rnd.uniform(0, 2 * math.pi); r0 = rnd.uniform(330, 400); r1 = r0 + rnd.uniform(140, 320); w = rnd.uniform(.012, .028)
        lines.append(f'<polygon points="{_pts([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)), (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))])}" fill="rgba(255,255,255,.4)"/>')
    inner = (''.join(lines)
             + f'<polygon points="{burst(335, 245)}" fill="{c["c_light"]}" fill-opacity=".5" stroke="#fff" stroke-opacity=".85" stroke-width="6" stroke-linejoin="round"/>'
             + f'<polygon points="{burst(250, 190, math.pi / n)}" fill="#fff" fill-opacity=".22"/>')
    return _svg(inner, masked=False)


def p_scales(c, rnd):
    r, out = 36, []
    for j in range(-1, 1000 // (r // 2) + 2):
        y = j * r * .55
        for i in range(-1, 600 // (2 * r) + 2):
            x = i * 2 * r + (r if j % 2 else 0)
            out.append(f'<path d="M{x - r},{y:.1f} A{r},{r} 0 0 0 {x + r},{y:.1f}" fill="none" stroke="rgba(255,255,255,.3)" stroke-width="3"/>'
                       f'<path d="M{x - r * .55:.1f},{y + r * .15:.1f} A{r * .62:.1f},{r * .62:.1f} 0 0 0 {x + r * .55:.1f},{y + r * .15:.1f}" fill="none" stroke="rgba(255,255,255,.13)" stroke-width="2"/>')
    return _svg(''.join(out))


def p_zigzag(c, rnd):
    out = []
    for k in range(-2, 1000 // 44 + 3):
        if k % 2: continue
        y0 = k * 44
        top = [(i * 30, y0 + (0 if i % 2 == 0 else 22)) for i in range(0, 22)]
        bot = [(x, y + 22) for x, y in reversed(top)]
        out.append(f'<polygon points="{_pts(top + bot)}" fill="rgba(255,255,255,.16)"/>')
        out.append(f'<polyline points="{_pts([(x, y + 33) for x, y in top])}" fill="none" stroke="{c["c_accent"]}" stroke-opacity=".5" stroke-width="2.5"/>')
    return _svg(''.join(out))


PATTERNS = dict(rays=p_rays, hex=p_hex, stars=p_stars, swirl=p_swirl, diamonds=p_diamonds, waves=p_waves, bubbles=p_bubbles,
                halftone=p_halftone, cracks=p_cracks, clouds=p_clouds, confetti=p_confetti, lowpoly=p_lowpoly,
                synthgrid=p_synthgrid, burst=p_burst, scales=p_scales, zigzag=p_zigzag)


# ---------------------------------------------------------------- the placeholder creature (400 × 400 drawing)
BODIES = {
    'round': dict(d='M200 120c95 0 140 70 140 140 0 70-60 105-140 105S60 330 60 260c0-70 45-140 140-140z', top=120, eye=250, mouth=312,
                  cheek=(85, 300), feet=(110, 345), shine='M110 180c20-30 50-42 80-44'),
    'bean': dict(d='M200 88c72 0 118 62 118 150 0 86-50 127-118 127S82 324 82 238c0-88 46-150 118-150z', top=88, eye=228, mouth=292,
                 cheek=(78, 280), feet=(122, 350), shine='M118 160c16-30 42-46 70-50'),
    'ghost': dict(d='M200 105c85 0 130 65 130 145v95' + 'q-13 22-26 0q-13-22-26 0' * 5 + 'V250c0-80 45-145 130-145z', top=105, eye=240, mouth=302,
                  cheek=(85, 290), feet=None, shine='M105 175c16-32 46-50 80-54', float=-16),
    'square': dict(d='M140 135h120a65 65 0 0 1 65 65v100a65 65 0 0 1-65 65H140a65 65 0 0 1-65-65V200a65 65 0 0 1 65-65z', top=135, eye=245, mouth=310,
                   cheek=(90, 298), feet=(110, 350), shine='M100 205c2-30 20-50 52-55'),
    'drop': dict(d='M200 92c38 62 132 100 132 178 0 62-54 95-132 95S68 332 68 270c0-78 94-116 132-178z', top=92, eye=262, mouth=322,
                 cheek=(84, 310), feet=(112, 350), shine='M128 210c12-28 32-52 56-74'),
}


def _star(cx, cy, ro, ri, n=5, rot=-math.pi / 2):
    return _pts([(cx + (ro if k % 2 == 0 else ri) * math.cos(rot + math.pi * k / n), cy + (ro if k % 2 == 0 else ri) * math.sin(rot + math.pi * k / n)) for k in range(2 * n)])


def crests(a, b, L):
    st = f'stroke="{L}" stroke-width="6" stroke-linejoin="round"'
    wing = 'M88 236C52 214 26 176 22 130c16 16 32 22 48 18-8 18-4 32 10 42-8 10-8 24 8 46z'
    petals = ''.join(f'<circle cx="{200 + 21 * math.cos(math.radians(72 * k - 90)):.1f}" cy="{80 + 21 * math.sin(math.radians(72 * k - 90)):.1f}" r="17" fill="{a}" {st}/>' for k in range(5))
    return {
        'feu': f'<path d="M200 70c20 30 50 40 40 90-10-20-25-25-30-15 10-40-25-45-10-75z M170 100c5 25 25 35 15 60-12-10-22-8-25 0-5-25 0-40 10-60z" fill="{a}" {st}/>',
        'eau': f'<path d="M150 130c20-60 80-80 110-60-30 10-40 30-35 60z" fill="{a}" {st}/>',
        'terre': f'<path d="M200 135V85M200 95c-25 0-40-18-40-40 25 0 40 15 40 40zM200 90c0-25 15-42 42-42 0 25-15 42-42 42z" fill="{a}" {st}/>',
        'air': f'<path d="M95 230c-50-30-70-80-55-110 25 30 45 40 75 45zM305 230c50-30 70-80 55-110-25 30-45 40-75 45z" fill="{a}" {st}/>',
        'couronne': f'<path d="M140 140l-10-70 40 35 30-55 30 55 40-35-10 70z" fill="{a}" {st}/><circle cx="200" cy="112" r="9" fill="#fff"/>',
        'cornes': f'<path d="M150 150c-38-14-56-52-46-92 20 26 42 40 70 46z M250 150c38-14 56-52 46-92-20 26-42 40-70 46z" fill="{a}" {st}/>'
                  f'<path d="M126 96c8 10 18 16 30 20M274 96c-8 10-18 16-30 20" stroke="{L}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".45"/>',
        'antennes': f'<path d="M178 132C170 100 150 80 135 62M222 132C230 100 250 80 265 62" fill="none" stroke="{L}" stroke-width="7" stroke-linecap="round"/>'
                    f'<circle cx="133" cy="58" r="17" fill="{a}" {st}/><circle cx="267" cy="58" r="17" fill="{a}" {st}/>'
                    f'<circle cx="127" cy="52" r="5" fill="#fff"/><circle cx="261" cy="52" r="5" fill="#fff"/>',
        'oreilles': f'<path d="M150 150c-30-40-42-104-22-126 30 14 44 70 42 122z M250 150c30-40 42-104 22-126-30 14-44 70-42 122z" fill="{b}" {st}/>'
                    f'<path d="M152 132c-16-30-22-70-14-86 14 12 22 48 22 84z M248 132c16-30 22-70 14-86-14 12-22 48-22 84z" fill="{a}"/>',
        'etoile': f'<path d="M200 128v-20" stroke="{L}" stroke-width="7" stroke-linecap="round"/><polygon points="{_star(200, 74, 40, 18)}" fill="{a}" {st}/>'
                  f'<circle cx="190" cy="66" r="5" fill="#fff"/>',
        'cristal': f'<path d="M168 138l8-62 22 58z M196 132l14-88 22 88z M226 138l16-56 14 60z" fill="{a}" {st}/>'
                   f'<path d="M207 62l-3 58M177 94l2 32M240 96l-5 32" stroke="#fff" stroke-opacity=".8" stroke-width="4" stroke-linecap="round"/>',
        'ailes': f'<path d="{wing}" fill="{a}" {st}/><path d="{wing}" fill="{a}" {st} transform="translate(400,0) scale(-1,1)"/>'
                 f'<path d="M30 140c12 26 26 46 44 58M370 140c-12 26-26 46-44 58" stroke="{L}" stroke-width="4" fill="none" opacity=".5"/>',
        'aureole': f'<ellipse cx="200" cy="76" rx="64" ry="16" fill="none" stroke="{L}" stroke-width="17"/>'
                   f'<ellipse cx="200" cy="76" rx="64" ry="16" fill="none" stroke="{a}" stroke-width="10"/>'
                   f'<ellipse cx="200" cy="76" rx="64" ry="16" fill="none" stroke="#fff" stroke-opacity=".85" stroke-width="3"/>',
        'fleur': f'<path d="M200 130c-2-16 2-28 8-36" stroke="{L}" stroke-width="7" fill="none" stroke-linecap="round"/>'
                 f'<path d="M204 112c-18-4-28 4-30 14 14 4 26-2 30-14z" fill="#7fd36a" {st}/>'
                 f'{petals}<circle cx="200" cy="80" r="13" fill="#ffe066" {st}/>',
        'piquants': f'<path d="M96 205 L104 142 L134 172 L146 104 L174 148 L196 84 L220 146 L250 104 L266 172 L296 142 L304 205 Z" fill="{a}" {st}/>',
        'plume': f'<path d="M204 128c4-54 42-96 96-104-6 42-42 88-92 108z" fill="{a}" {st}/>'
                 f'<path d="M210 124c20-32 46-60 76-86M236 90l-14-8M252 72l-12-10M262 100l-12-4M276 82l-10-4" stroke="{L}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        'bulle': '',
    }


def eyes(kind, ey, b, L):
    st = f'stroke="{L}" stroke-width="6"'
    two = lambda f: f(155) + f(245)
    if kind == 'cyclope':
        return (f'<ellipse cx="200" cy="{ey}" rx="54" ry="58" fill="#fff" {st}/><circle cx="206" cy="{ey + 10}" r="28" fill="#2a1406"/>'
                f'<circle cx="217" cy="{ey - 2}" r="9" fill="#fff"/><circle cx="196" cy="{ey + 22}" r="4" fill="#fff"/>')
    if kind == 'happy':
        return two(lambda x: f'<path d="M{x - 26},{ey + 10} Q{x},{ey - 26} {x + 26},{ey + 10}" fill="none" stroke="{L}" stroke-width="9" stroke-linecap="round"/>')
    if kind == 'sleepy':
        return two(lambda x: f'<ellipse cx="{x}" cy="{ey}" rx="32" ry="30" fill="#fff"/><circle cx="{x + 4}" cy="{ey + 10}" r="15" fill="#2a1406"/>'
                             f'<path d="M{x - 34},{ey + 3} A34,31 0 0 1 {x + 34},{ey + 3} Z" fill="{b}"/>'
                             f'<ellipse cx="{x}" cy="{ey}" rx="32" ry="30" fill="none" {st}/>'
                             f'<path d="M{x - 34},{ey + 3} H{x + 34}" stroke="{L}" stroke-width="6" stroke-linecap="round"/>')
    base = two(lambda x: f'<ellipse cx="{x}" cy="{ey}" rx="34" ry="42" fill="#fff" {st}/>')
    if kind == 'star':
        return base + two(lambda x: f'<circle cx="{x + 6}" cy="{ey + 6}" r="22" fill="#2a1406"/><polygon points="{_star(x + 12, ey - 2, 11, 4, 4, 0)}" fill="#fff"/>'
                                    f'<circle cx="{x - 2}" cy="{ey + 16}" r="3.5" fill="#fff"/>')
    if kind == 'fierce':
        return (base + two(lambda x: f'<circle cx="{x + (6 if x < 200 else -6)}" cy="{ey + 10}" r="17" fill="#2a1406"/><circle cx="{x + (11 if x < 200 else -1)}" cy="{ey + 3}" r="5.5" fill="#fff"/>')
                + f'<path d="M118 {ey - 50} L184 {ey - 34}M282 {ey - 50} L216 {ey - 34}" stroke="{L}" stroke-width="12" stroke-linecap="round"/>')
    return base + two(lambda x: f'<circle cx="{x + 8}" cy="{ey + 8}" r="18" fill="#2a1406"/><circle cx="{x + 15}" cy="{ey}" r="6" fill="#fff"/>')


def mouth(kind, my, L):
    st = f'stroke="{L}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"'
    if kind == 'fang':
        return f'<path d="M180 {my}c12 12 28 12 40 0" fill="none" {st}/><path d="M203 {my + 7}l7 12 6-12z" fill="#fff" stroke="{L}" stroke-width="3" stroke-linejoin="round"/>'
    if kind == 'open':
        return f'<ellipse cx="200" cy="{my + 6}" rx="16" ry="14" fill="#5a1020" {st}/><ellipse cx="200" cy="{my + 13}" rx="9" ry="5" fill="#ff7a8a"/>'
    if kind == 'cat':
        return f'<path d="M177 {my}c6 10 17 10 23 0c6 10 17 10 23 0" fill="none" {st}/>'
    if kind == 'grin':
        return f'<path d="M172 {my - 4}h56c0 24-14 34-28 34s-28-10-28-34z" fill="#5a1020" {st}/><path d="M176 {my - 1}h48v8h-48z" fill="#fff"/>'
    return f'<path d="M180 {my}c12 12 28 12 40 0" fill="none" {st}/>'


def creature(look, c):
    """an original placeholder mascot: body + crest + eyes + mouth, in the pack's colours"""
    B = BODIES[look.get('body', 'round')]; a, b, L = c['c_accent'], c['c_body'], LINE
    dy = B['top'] - 120; fl = B.get('float', 0)
    crest = look.get('crest', 'feu'); cr = crests(a, b, L)[crest]
    shadow = (f'<ellipse cx="200" cy="384" rx="86" ry="11" fill="rgba(0,0,0,.2)"/>' if fl else
              f'<ellipse cx="200" cy="372" rx="120" ry="18" fill="rgba(0,0,0,.25)"/>')
    feet = ''
    if B['feet']:
        fx, fy = B['feet']
        feet = f'<path d="M{fx} {fy}c0 18 25 22 35 8M{400 - fx} {fy}c0 18-25 22-35 8" fill="{b}" stroke="{L}" stroke-width="6" stroke-linejoin="round"/>'
    cdx, cy = B['cheek']
    cheeks = '' if look.get('eyes') == 'cyclope' else (f'<ellipse cx="{200 - cdx}" cy="{cy}" rx="16" ry="9" fill="rgba(255,120,120,.45)"/>'
                                                        f'<ellipse cx="{200 + cdx}" cy="{cy}" rx="16" ry="9" fill="rgba(255,120,120,.45)"/>')
    bubble = ''
    if crest == 'bulle':
        bcy, br = (B['top'] + 365) / 2, (365 - B['top']) / 2 + 30
        bubble = (f'<circle cx="200" cy="{bcy:.0f}" r="{br:.0f}" fill="rgba(255,255,255,.12)" stroke="#fff" stroke-opacity=".75" stroke-width="5"/>'
                  f'<path d="M{200 - br * .72:.0f} {bcy - br * .2:.0f}A{br * .78:.0f} {br * .78:.0f} 0 0 1 {200 - br * .2:.0f} {bcy - br * .74:.0f}" fill="none" stroke="#fff" stroke-opacity=".9" stroke-width="9" stroke-linecap="round"/>'
                  f'<ellipse cx="200" cy="{bcy + br - 8:.0f}" rx="{br * .55:.0f}" ry="14" fill="{a}" stroke="{L}" stroke-width="6"/>')
    body = (f'<g transform="translate(0,{dy})">{cr}</g>'
            f'<path d="{B["d"]}" fill="{b}" stroke="{L}" stroke-width="7"/>'
            f'<path d="{B["shine"]}" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="12" stroke-linecap="round"/>'
            + eyes(look.get('eyes', 'round'), B['eye'], b, L) + mouth(look.get('mouth', 'smile'), B['mouth'], L) + cheeks + feet + bubble)
    return (f'<svg viewBox="0 0 400 400" width="430" height="430" overflow="visible">{shadow}'
            f'<g transform="translate(0,{fl})">{body}</g></svg>')


def _font(fam, file, w):
    d = base64.b64encode(open(os.path.join(HERE, 'fonts', file), 'rb').read()).decode()
    return f"@font-face {{ font-family: '{fam}'; font-weight: {w}; src: url(data:font/woff2;base64,{d}) format('woff2'); }}"


FONTS = _font('Lilita One', 'lilita-one-latin-400-normal.woff2', 400) + '\n' + _font('Nunito', 'nunito-latin-900-normal.woff2', '800 900')


def sparkles(seed, holo):
    rnd = random.Random(seed); n = 14 if holo else 7; out = []
    for _ in range(n):
        x, y, s = rnd.uniform(40, 540), rnd.uniform(110, 860), rnd.uniform(0.5, 1.3)
        out.append(f'<div class="sparkle" style="left:{x:.0f}px;top:{y:.0f}px;transform:scale({s:.2f});opacity:{rnd.uniform(.6, 1):.2f}"></div>')
    return ''.join(out)


def render(packs):
    from playwright.sync_api import sync_playwright
    tpl = open(os.path.join(HERE, 'booster.html'), encoding='utf8').read()
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 700, 'height': 1100}, device_scale_factor=2)
        for pk in packs:
            v = dict(pk['colors'])
            look = pk.get('look') or dict(body='round', crest=pk.get('crest', 'feu'), eyes='round', mouth='smile')
            rnd = random.Random(pk['id'] + ':pattern')
            v.update(shape=pack_shape(), holo=str(pk.get('holo', 0)), fine=pk.get('fine', ''),
                     sparkles=sparkles(pk['id'], True), pattern=PATTERNS[pk.get('pattern', 'rays')](pk['colors'], rnd),
                     rings='<div class="ring"></div><div class="ring r2"></div>' if pk.get('rings', True) else '')
            v['art'] = img_tag(pk['art']) if pk.get('art') else creature(look, pk['colors'])
            v['logo'] = img_tag(pk['logo']) if pk.get('logo') else f'<div class="l1">{pk["title"]}</div><div class="l2">{pk["subtitle"]}</div>'
            v['fonts'] = FONTS
            html = tpl
            for k, val in v.items(): html = html.replace('{{' + k + '}}', val)
            pg.set_content(html, wait_until='networkidle')
            pg.wait_for_timeout(300)
            pg.locator('.stage').screenshot(path=os.path.join(OUT, pk['id'] + '.png'), omit_background=True)
            print('ok', pk['id'])
        b.close()


if __name__ == '__main__':
    packs = json.load(open(os.path.join(HERE, 'boosters.json'), encoding='utf8'))['packs']
    want = sys.argv[1:]
    render([p for p in packs if not want or p['id'] in want])
