"""0.98.3: the TTG cards and booster packs = Ankama's official pictures, read from dofusretrotools.com (api/ency/consumables,
scope ttg; downloaded once into work/ttg98/). Cards: the PNG without its transparent margins, at its own size ->
game/assets/ttg/c<number>.webp (loaded one by one: the binder holds 464). Packs: the SVG (48: one for each of the 44
families of C.ttg.cards, four by rarity) rendered at Z x its size, turned upright (the official pack leans by ANGLE), cut to
W x H -> game/assets/ttg/p<i>.webp + SPR.boosters {n, w, h, names}: names[i] = its family (C.ttg.cards[].fam) or r0..r3.
Stops if a card's family or rarity differs from the site's, or a family has no pack.
usage: python tools/assets/build_ttg098.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, io, re, json, time, urllib.request, urllib.parse
from PIL import Image
from playwright.sync_api import sync_playwright
import sprio

G = f'{ROOT}/game'
W_ = f'{ROOT}/work/ttg98'
SITE = 'https://dofusretrotools.com'
ANGLE, W, H, Z = 18.2, 400, 660, 3
RARITY = {'Commune': 'r0', 'Rare': 'r1', 'Epique': 'r2', 'Ultime': 'r3'}


def fetch(path):
    return urllib.request.urlopen(urllib.request.Request(SITE + urllib.parse.quote(path, safe="/?=&"), headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()


def download():
    os.makedirs(f'{W_}/cards', exist_ok=True); os.makedirs(f'{W_}/packs', exist_ok=True)
    if not os.path.exists(f'{W_}/site.json'): open(f'{W_}/site.json', 'wb').write(json.dumps(json.loads(fetch('/api/ency/consumables?all=true&scope=ttg'))['consumables'], ensure_ascii=False).encode('utf8'))
    L = json.load(open(f'{W_}/site.json', encoding='utf8'))
    for x in L:
        u = x['imageUrl']; m = re.search(r'No\.(\d+)', x['name'])
        f = f"{W_}/cards/{m.group(1)}.png" if m else f"{W_}/packs/{u.rsplit('paquet_', 1)[1]}"
        if not os.path.exists(f): open(f, 'wb').write(fetch(u)); time.sleep(0.05)
    return L


def audit(L):
    C = json.load(open(f'{G}/data/content.json', encoding='utf8'))['ttg']['cards']
    site = {int(m.group(1)): (x['imageUrl'].split('/')[4], x['typeId'] - 119) for x in L if (m := re.search(r'No\.(\d+)', x['name']))}
    bad = [c['id'] for c in C if site.get(c['id']) != (c['fam'], c['r'])]
    if bad or len(site) != len(C): sys.exit(f'cards that differ from the site: {bad}')
    packs = sorted(f[:-4] for f in os.listdir(f'{W_}/packs'))
    no = {c['fam'] for c in C} - set(packs)
    if no: sys.exit(f'families without a pack: {no}')
    return C, packs


def cards(C):
    for f in os.listdir(f'{G}/assets/ttg'):
        if re.fullmatch(r'ttg_\d+\.webp|c\d+\.webp', f): os.remove(f'{G}/assets/ttg/{f}')
    n = 0
    for c in C:
        im = Image.open(f"{W_}/cards/{c['id']:03d}.png").convert('RGBA'); im = im.crop(im.getbbox())
        im.save(f"{G}/assets/ttg/c{c['id']}.webp", 'WEBP', quality=88, method=6); n += os.path.getsize(f"{G}/assets/ttg/c{c['id']}.webp")
    print('cards', len(C), n // 1024, 'KB', flush=True)


def packs(names):
    for f in os.listdir(f'{G}/assets/ttg'):
        if re.fullmatch(r'p\d+\.webp', f): os.remove(f'{G}/assets/ttg/{f}')
    n, out = 0, []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 700, 'height': 700}, device_scale_factor=Z)
        page = f'{W_}/pack.html'; open(page, 'w', encoding='utf8').write('<body style="margin:0;background:transparent"><img id="p" style="position:absolute;left:137px;top:117px;width:425.8px;height:466px"></body>')
        pg.goto('file:///' + page)
        for i, nm in enumerate(names):
            pg.evaluate("""([u, a]) => new Promise(r => { const e = document.getElementById('p'); e.onload = r; e.style.transform = `rotate(${a}deg)`; e.src = u; })""",
                        ['file:///' + urllib.parse.quote(f'{W_}/packs/{nm}.svg'), ANGLE])
            im = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert('RGBA'); im = im.crop(im.getbbox()).resize((W, H), Image.LANCZOS)
            im.save(f'{G}/assets/ttg/p{i}.webp', 'WEBP', quality=88, method=6); n += os.path.getsize(f'{G}/assets/ttg/p{i}.webp'); out.append(RARITY.get(nm, nm))
        b.close()
    os.remove(page)
    sprio.update(lambda S: (S.__setitem__('boosters', {'n': len(out), 'w': W, 'h': H, 'names': out}), S.pop('ttg', None)))
    print('packs', len(out), n // 1024, 'KB', flush=True)


if __name__ == '__main__':
    C, names = audit(download())
    cards(C); packs(names)
    print('ok')
