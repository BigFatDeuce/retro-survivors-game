"""0.34: the TTG cards (Trading card game of Dofus Retro: 464 numbered cards, 4 rarities). The official list
(work/ttg_cards.json: number, name, rarity, family) was read from dofusretrotools.com (api/ency/consumables?scope=ttg).
Each card's picture is the monster's own client artwork (clips/artworks/big/<gfx>.swf), rendered natively at A px and
framed on the drawing (like build_art21); the few cards with no client artwork (Halouine monsters, later NPCs) keep the
picture of the official card (its art window, downloaded once into work/ttg_img/). The card itself (frame, stars,
number, name) is drawn by the game (CSS). -> assets/ttg/ttg_<n>.webp + SPR.ttg, and work/ttg34.json (the card data
patch_033 puts in C.ttg.cards, names in the 7 languages from the client's monster names).
usage: python tools/assets/build_ttg34.py [A=300]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, re, unicodedata, urllib.request, urllib.parse
from PIL import Image
import stage as ST, sprio
from build_art21 import size1

G = f'{ROOT}/game'
RAW = f'{ROOT}/raw/rc/clips/artworks/big'
LANGS = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
SITE = 'https://dofusretrotools.com'


def norm(s): return unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode().replace('-', ' ').replace("'", ' ').strip()


def main(A=300):
    cards = json.load(open(f'{ROOT}/work/ttg_cards.json'))
    M = {lg: json.load(open(f'{ROOT}/work/lang_json/monsters_{lg}.json'))['M'] for lg in LANGS}
    byname = {}
    for k, v in M['fr'].items():
        if isinstance(v, dict) and 'n' in v: byname.setdefault(norm(v['n']), (k, v.get('g')))
    jobs, fall = [], []
    for c in cards:
        m = byname.get(norm(c['name'])); c['key'] = f"t{c['no']}"
        c['names'] = {lg: (M[lg].get(m[0], {}).get('n') if m else None) or c['name'] for lg in LANGS}
        p = f'{RAW}/{m[1]}.swf' if m else None
        if p and os.path.exists(p) and size1(p) > 0: jobs.append((p, [dict(key=c['key'], root=True, zoom=A * 2 / size1(p), frames=[0], n=1)]))
        else: fall.append(c)
    print(len(jobs), 'client artworks,', len(fall), 'official pictures', flush=True)
    res = {}
    for i in range(0, len(jobs), 40):
        res.update(ST.stage_batch(jobs[i:i + 40], f'{ROOT}/work/ttg34/{i}', prune=True)); print('rendered', min(i + 40, len(jobs)), '/', len(jobs), flush=True)
    again = []   # framed on the drawing when the SWF declares a much bigger frame (as build_art21)
    for p, js in jobs:
        j = js[0]; r = res.get(j['key']); im = r['imgs'][0] if r and r['imgs'] else None
        if im is None or not im.getbbox(): continue
        x0, y0, x1, y1 = im.getbbox(); big = max(x1 - x0, y1 - y0)
        if big >= A * 2 * 0.9: continue
        ox, oy = r['meta']['origin']; k = j['zoom'] / 20.0; pad = 4
        again.append((p, [dict(j, zoom=j['zoom'] * A * 2 / big, bounds=((x0 - pad - ox) / k, (x1 + pad - ox) / k, (y0 - pad - oy) / k, (y1 + pad - oy) / k))]))
    for i in range(0, len(again), 40):
        res.update(ST.stage_batch(again[i:i + 40], f'{ROOT}/work/ttg34b/{i}', prune=True)); print('re-rendered', min(i + 40, len(again)), flush=True)
    items = []
    for c in cards:
        r = res.get(c['key']); im = r['imgs'][0] if r and r['imgs'] else None
        if im is not None and im.getbbox():
            im = im.crop(im.getbbox()); s = A / max(im.size)
            items.append((c['key'], im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS))); c['src'] = 'client'
        else:
            if c not in fall: fall.append(c)
    os.makedirs(f'{ROOT}/work/ttg_img', exist_ok=True)
    for c in fall:
        f = f"{ROOT}/work/ttg_img/{c['no']}.png"
        if not os.path.exists(f):
            req = urllib.request.Request(SITE + urllib.parse.quote(c['img']), headers={'User-Agent': 'Mozilla/5.0'})
            open(f, 'wb').write(urllib.request.urlopen(req, timeout=30).read())
        im = Image.open(f).convert('RGBA'); w, h = im.size
        art = im.crop((round(w * 0.1), round(h * 0.17), round(w * 0.9), round(h * 0.7)))   # the art window of the official card
        items.append((c['key'], art)); c['src'] = 'site'
    os.makedirs(f'{G}/assets/ttg', exist_ok=True)
    for f in os.listdir(f'{G}/assets/ttg'):
        if f.startswith('ttg_'): os.remove(f'{G}/assets/ttg/{f}')
    NF, n, rest = {}, 0, items
    while rest:
        atlas, pos = ST.pack(rest, maxw=4096)
        fit = [(k, im) for k, im in rest if k in pos and pos[k][1] + pos[k][3] <= 4096]
        if atlas.height > 4096: atlas = atlas.crop((0, 0, atlas.width, 4096))
        atlas.save(f'{G}/assets/ttg/ttg_{n}.webp', 'WEBP', quality=86, method=6)
        for k, _ in fit: x, y, w, h = pos[k]; NF[k] = [n, x, y, w, h]
        print('sheet', n, atlas.size, len(fit), os.path.getsize(f'{G}/assets/ttg/ttg_{n}.webp'), flush=True)
        rest = [(k, im) for k, im in rest if k not in NF]; n += 1
    sprio.update(lambda S: S.__setitem__('ttg', {'sheets': n, 'f': NF}))
    out = [dict(id=c['no'], name=c['names'], r=c['rarity'], fam=c['family'], art=c['key']) for c in cards if c['key'] in NF]
    json.dump(out, open(f'{ROOT}/work/ttg34.json', 'w'), ensure_ascii=False)
    print('cards', len(out), {s: sum(1 for c in cards if c.get('src') == s) for s in ('client', 'site')})


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 300)
