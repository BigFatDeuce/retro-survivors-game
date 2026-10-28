"""0.60: the spell fusions' Dofus Retro effects: client spell clips (clips/spells/<n>.swf, the clip of the real spell each
fusion is named after: Flèche Destructrice 911, Épée du destin 814, Pandatak 1214…) rendered from their root timeline
(stop() actions honoured) at zoom 2.4 -> assets/fx/<n>.webp + SPR.fx['<n>'] = {w, h, zoom, anims: {root: {fps, f}}}.
usage: python tools/assets/build_fx060.py n… | preview n… out.png"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os
from PIL import Image
import swflib as S, timeline as TL, stage as ST, sprio

G = f'{ROOT}/game'
Z = 2.4


def render(n):
    """{anim: render}: the clip's exported 'shoot' (impact) and 'move' (flying) symbols like the 0.1x fx sheets, else
    its root timeline"""
    src = f'{ROOT}/raw/rc/clips/spells/{n}.swf'
    sw = S.read_swf(src); ex = S.exports(sw['tags']); tl = TL.Timeline(sw)
    jobs = [dict(key=k, sym=k, zoom=Z, n=tl.eff_frames(ex[k])) for k in ('shoot', 'move', 'duplicate') if k in ex]   # (0.60: 'duplicate' = Rayon Obscur's 805, one on every cell)
    if not jobs:
        sw['tags'].append(ST.root_sprite(sw)); jobs = [dict(key='root', root=True, zoom=Z, n=TL.Timeline(sw).eff_frames(ST.ROOT_ID))]
    return ST.stage_render(src, jobs, f'{ROOT}/work/fx060/{n}', holds=True), sw['rate']


def build(n):
    R, rate = render(n); items = []; anims = {}
    for k, r in R.items():
        fr = []
        for i, im in enumerate(r['imgs']):
            if im is None or not im.getbbox(): fr.append(None); continue
            c, ox, oy = ST.crop(im, r['meta']['origin']); items.append(((k, i), c)); fr.append((k, i, ox, oy))
        while fr and fr[-1] is None: fr.pop()   # (no empty tail: the effect ends with its last drawing)
        if fr: anims[k] = fr
    atlas, pos = ST.pack(items, maxw=2048)
    atlas.save(f'{G}/assets/fx/{n}.webp', 'WEBP', quality=88, method=6)
    A = {}
    for k, fr in anims.items():
        A[k] = dict(fps=rate, f=[[0, 0, 1, 1, 0, 0] if o is None else [*pos[(o[0], o[1])], round(o[2], 2), round(o[3], 2)] for o in fr])
    print(n, {k: len(v['f']) for k, v in A.items()}, atlas.size, os.path.getsize(f'{G}/assets/fx/{n}.webp') // 1024, 'KB', flush=True)
    return dict(w=atlas.width, h=atlas.height, zoom=Z, anims=A)


def preview(ns, out):
    rows = []
    for n in ns:
        R, _ = render(n); r = R.get('shoot') or R.get('root') or next(iter(R.values())); ims = [im for im in r['imgs'] if im is not None and im.getbbox()]
        pick = [ims[int(k * (len(ims) - 1) / 7)] for k in range(8)] if ims else []
        row = Image.new('RGBA', (8 * 170, 170), (34, 40, 30, 255))
        for k, im in enumerate(pick):
            im = im.crop(im.getbbox()); s = min(1, 160 / max(im.size)); im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
            row.alpha_composite(im, (k * 170 + (170 - im.width) // 2, (170 - im.height) // 2))
        rows.append(row); print(n, len(ims), 'frames', flush=True)
    sheet = Image.new('RGBA', (8 * 170, 170 * len(rows)))
    for i, row in enumerate(rows): sheet.paste(row, (0, i * 170))
    sheet.save(out)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'preview': preview([int(x) for x in a[1:-1]], a[-1])
    else:
        out = {str(n): build(int(n)) for n in a}
        sprio.update(lambda S_: S_['fx'].update(out))
