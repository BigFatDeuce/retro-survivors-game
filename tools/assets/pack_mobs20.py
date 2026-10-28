"""v2.0: the ~240 monster sheets are packed into a few images per zone (the artifact holds at most ~500 files): every
sheet keeps its own frames, now relative to the pack (SPR.mobs[key].src = 'mobs/<pack>.webp').
Groups: 'common' (what every run loads), one or more packs per zone (its monsters and bosses, in zone order; a monster
shared with an earlier zone stays in that zone's pack), 'misc' for the rest. Usage: pack_mobs20.py [--dry]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json
import stage as ST
from PIL import Image

G = f'{ROOT}/game'
MAXH = 4096


def layout_h(sizes, maxw=4096, pad=2):
    """height of ST.pack's shelf layout for these sizes"""
    x = y = 0; rowh = 0
    for w, h in sorted(sizes, key=lambda e: (-e[1], -e[0])):
        if x + w + pad > maxw and x > 0: y += rowh + pad; x = 0; rowh = 0
        x += w + pad; rowh = max(rowh, h)
    return y + rowh


def map_keys(C, m):
    M = C['monsters']; B = C['bosses']; k = set()
    for w in m['waves']:
        for mid, _ in w[2]: k.add(M[mid]['sprite'])
    for e in m['events']: k.add(M[e[2]]['sprite'])
    for t, b in m['bosses']:
        bd = B[b]; k.add(bd['sprite'])
        for ab in bd['abilities']:
            if ab.get('mob'): k.add(M[ab['mob']]['sprite'])
            for p in ab.get('pool') or []: k.add(M[p]['sprite'])
    if m.get('secret'): k.add(B[m['secret'][1]]['sprite'])
    for r, _ in m.get('rare') or []: k.add(M[r]['sprite'])
    for mm in list(k):   # summoners' summons
        for x in M.values():
            if x['sprite'] == mm and x.get('atk') and x['atk'].get('mob'): k.add(M[x['atk']['mob']]['sprite'])
    return k


def common_keys(C):
    k = {C['monsters']['tofu']['sprite'], C['chestSprite'], C.get('totSprite') or '1010_tot', C['bosses']['bouftou_royal']['sprite']}
    if C.get('doom'): k |= {C['bosses'][C['doom']['boss']]['sprite'], C['doom']['crowSprite']}
    for a in C['allies'].values(): k.add(a['sprite'])
    if C.get('bombSprite'): k.add(C['bombSprite'])
    return k


def summon_keys(C):
    k = set()
    for s in C['spells'].values():
        if s.get('t') == 'summon':
            if s['base'].get('spriteKey'): k.add(s['base']['spriteKey'])
            for v in (s.get('spriteKeyBy') or {}).values(): k.add(v)
    return k


def main(dry=False):
    C = json.load(open(f'{G}/data/content.json')); SPR = json.load(open(f'{G}/data/sprites.json'))
    mobs = {k: v for k, v in SPR['mobs'].items() if not v.get('src')}
    only = next((a.split('=', 1)[1].split(',') for a in sys.argv if a.startswith('--keys=')), None)   # (0.50: pack only these sheets, e.g. a new zone's)
    if only: mobs = {k: v for k, v in mobs.items() if k in only}
    assigned = {}; groups = []
    def add(name, keys):
        ks = sorted(k for k in keys if k in mobs and k not in assigned)
        for k in ks: assigned[k] = name
        if ks: groups.append((name, ks))
    add('common', common_keys(C))
    add('summons', summon_keys(C))
    # the zone sheets are grouped by the exact set of zones that use them: a zone never loads a sheet it does not need
    need = {m['id']: map_keys(C, m) for m in C['maps']}
    sig = {}
    for z, ks in need.items():
        for k in ks: sig.setdefault(k, set()).add(z)
    order = [m['id'] for m in C['maps']]
    for zs in sorted({frozenset(v) for v in sig.values()}, key=lambda f: (len(f), min(order.index(z) for z in f))):
        add('_'.join(sorted(zs, key=order.index)) if len(zs) <= 2 else f"{len(zs)}z_{'_'.join(sorted(zs, key=order.index))[:40]}",
            {k for k, v in sig.items() if frozenset(v) == zs})
    if not only: add('misc', set(mobs))
    # what each zone's run loads beyond its own needs
    for m in C['maps']:
        need_ = map_keys(C, m) | common_keys(C); packs = {assigned.get(k) for k in need_ if k in assigned}
        extra = sum(1 for k, g in assigned.items() if g in packs and k not in need_)
        print(f"{m['id']:14s} packs {len(packs)} extra sheets {extra}")
    print('groups', len(groups), [(g, len(k)) for g, k in groups])
    if dry: return
    files = []
    for name, ks in groups:
        items = []
        for k in ks:
            p = f'{G}/assets/mobs/{k}.webp'
            if not os.path.exists(p): print('missing', p); continue
            items.append((k, Image.open(p).convert('RGBA')))
        # split into packs no taller than MAXH (shelf packing of whole sheets; layout computed without pixels first)
        part = 0
        while items:
            items.sort(key=lambda e: (-e[1].height, -e[1].width))
            chosen = []; rest = []
            for it in items:
                if layout_h([c[1].size for c in chosen] + [it[1].size]) <= MAXH or not chosen: chosen.append(it)
                else: rest.append(it)
            atlas, pos = ST.pack(chosen, maxw=4096, pad=2)
            pname = f'pack_{name}' + (f'_{part}' if part or rest else '')
            atlas.save(f'{G}/assets/mobs/{pname}.webp', 'WEBP', quality=88, method=6)
            for k, im in chosen:
                x, y, w, h = pos[k]; meta = SPR['mobs'][k]
                for a in meta['anims'].values():
                    a['f'] = [[f[0] + x, f[1] + y] + list(f[2:]) for f in a['f']]
                meta['src'] = f'mobs/{pname}.webp'; meta['w'], meta['h'] = atlas.width, atlas.height
            files.append((pname, atlas.size, os.path.getsize(f'{G}/assets/mobs/{pname}.webp'), len(chosen)))
            print(*files[-1], flush=True)
            items = rest; part += 1
    import sprio
    sprio.update(lambda S: S.__setitem__('mobs', SPR['mobs']))
    for k in assigned:
        p = f'{G}/assets/mobs/{k}.webp'
        if os.path.exists(p): os.remove(p)
    for f in files: print(*f)
    print('packs', len(files), 'MB', round(sum(f[2] for f in files) / 1e6, 1))


if __name__ == '__main__':
    main('--dry' in sys.argv)
