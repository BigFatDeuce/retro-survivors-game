"""0.51: every monster sheet in HD, like the 0.50 zones': at 2560x1440 a monster is drawn ~2.9 screen px per Dofus px
(zoom 1.92 x ES 1.5) and a boss ~4.6, but the sheets were rendered at 2.4 / 3.0 (blown up x1.2 / x1.5). The standard
sheets (walk / die / attack [/ static]) are re-rendered from the client sprites at 3.0 (monsters) and 4.5 (bosses),
under the same keys (content keeps its sprite names); the special ones (recoloured Pious, ToT, Drago armour, menu
critters, Musha…) are kept as they are. Then everything is repacked.
usage: python tools/assets/hd_mobs51.py [render|pack|all] [WORKERS=3]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, re, subprocess
from PIL import Image

G = f'{ROOT}/game'
STD = {'walkR', 'walkL', 'dieR', 'atkR', 'staticR'}
ZM, ZB = 3.0, 4.5
KEEP_LOOSE = {'1153_z120', '1042_z48', '1558_z48'}   # loaded on their own (Musha's scene, the main menu's critters)


def targets():
    M = json.load(open(f'{G}/data/sprites.json'))['mobs']
    out = []
    for k, v in M.items():
        m = re.fullmatch(r'(\d+)_z(\d+)', k)
        if not m or v['zoom'] not in (2.4, 3.0) or not set(v['anims']) <= STD: continue
        out.append((k, int(m.group(1)), v['zoom'] == 3.0 or 'staticR' in v['anims']))
    return out


def render_one(k, gfx, boss):
    import build_mobs20 as B, sprio
    z0 = ZB if boss else ZM
    for z in (z0, z0 * 0.88):   # (a sheet too tall for one 4096 atlas: a little less zoom; else it keeps its old one)
        try: meta = B.build(gfx, k, round(z, 2), boss); break
        except SystemExit as e: print(e, flush=True)
    else: return
    sprio.update(lambda S: S['mobs'].__setitem__(k, meta))


def unpack_kept():
    """the sheets not re-rendered that live in a pack: cut out of it as loose sheets (frames made relative again)"""
    import sprio
    S = json.load(open(f'{G}/data/sprites.json')); M = S['mobs']; packs = {}; n = 0
    for k, v in M.items():
        src = v.get('src') or ''
        if not src.startswith('mobs/pack_'): continue
        fr = [f for a in v['anims'].values() for f in a['f'] if f[2] > 1]
        x0, y0 = min(f[0] for f in fr), min(f[1] for f in fr); x1, y1 = max(f[0] + f[2] for f in fr), max(f[1] + f[3] for f in fr)
        im = packs.setdefault(src, Image.open(f'{G}/assets/{src}').convert('RGBA')).crop((x0, y0, x1, y1))
        im.save(f'{G}/assets/mobs/{k}.webp', 'WEBP', quality=88, method=6)
        for a in v['anims'].values(): a['f'] = [[f[0] - x0, f[1] - y0] + list(f[2:]) if f[2] > 1 else [0, 0, 1, 1, 0, 0] for f in a['f']]
        v.pop('src'); v['w'], v['h'] = im.size; n += 1
    sprio.update(lambda T: T.__setitem__('mobs', M))
    print('unpacked', n, flush=True)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what == 'one':   # (worker) one sheet
        render_one(sys.argv[2], int(sys.argv[3]), sys.argv[4] == '1'); sys.exit()
    if what in ('render', 'all'):
        T = targets(); W = int(os.environ.get('WORKERS', '3')); print(len(T), 'sheets to re-render', flush=True)
        procs = []
        for i, (k, gfx, boss) in enumerate(T):
            while len([p for p in procs if p.poll() is None]) >= W:
                import time; time.sleep(0.5)
            procs.append(subprocess.Popen([sys.executable, __file__, 'one', k, str(gfx), '1' if boss else '0'], stdout=subprocess.DEVNULL))
            if i % 10 == 0: print(i, '/', len(T), flush=True)
        for p in procs: p.wait()
        bad = [T[i][0] for i, p in enumerate(procs) if p.returncode]
        print('rendered; failed:', bad, flush=True)
    if what in ('pack', 'all'):
        unpack_kept()
        for f in os.listdir(f'{G}/assets/mobs'):
            if f.startswith('pack_'): os.remove(f'{G}/assets/mobs/{f}')
        M = json.load(open(f'{G}/data/sprites.json'))['mobs']
        keys = [k for k, v in M.items() if not v.get('src') and k not in KEEP_LOOSE]
        subprocess.run([sys.executable, f'{ROOT}/tools/assets/pack_mobs20.py', '--keys=' + ','.join(keys)], check=True)
