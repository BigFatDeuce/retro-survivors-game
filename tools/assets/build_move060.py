"""0.60: moves at 60 fps, as in Dofus Retro Remastered. The up-to-date client's sprites run at 60 fps (the
1.41.9 client the game was built from: 20 fps; a run is 30 frames instead of 10), so:
  chars [key…]   every '<key>_r' sheet (characters, hat variants) is rendered again from the up-to-date client with the
                 five runs (runR, runL, runF, runB, runS) at their 60 fps, base + 3 colour-zone passes and the accessory
                 anchors of every frame (hats, capes, pets follow each of the 60 frames). CharSprite takes the runs from
                 this sheet first (assets.js sheetFor).
  pets [sym…]    every pet's walks (WR WL WF WB WS) again from the up-to-date client, all their frames at 60 fps (the
                 0.60 new pets had been cut to 24 frames played at 20 fps: a third of the step, slowed down)
  bosses         the humanoid bosses' walks (Dark Vlad, Goultard, Qu'Tan) at 60 fps, added to their sheets
Each step keeps what it rendered in work/move060/ (it resumes), then writes sprites.json once at the end.
usage: python tools/assets/build_move060.py chars|pets|bosses|all [keys…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, collections
import numpy as np
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_acc060 as BA
from PIL import Image

G = f'{ROOT}/game'
from _root import CLIENT as NEW   # the up-to-date installed client (_root.py)
NSPR = f'{NEW}/clips/sprites'
WORK = f'{ROOT}/work/move060'
Z = 4.8
SLOT = {1: 1, 2: 2, 3: 3}   # (hat, cape, pet; no weapon in the runs)
RUNS = ('runR', 'runL', 'runF', 'runB', 'runS')
MAXF = 90


PART = os.environ.get('MOVE_PART', '')   # (several processes side by side: each keeps its own file, apply merges them)


def done_file(kind, part=None): return f'{WORK}/{kind}{PART if part is None else part}_meta.json'


def load_done(kind, merged=True):
    import glob as _g
    out = {}
    for p in (sorted(_g.glob(f'{WORK}/{kind}*_meta.json')) if merged else [done_file(kind)]):
        if os.path.exists(p): out.update(json.load(open(p)))
    return out


def save_done(kind, d):
    os.makedirs(WORK, exist_ok=True); json.dump(d, open(done_file(kind) + '.tmp', 'w')); os.replace(done_file(kind) + '.tmp', done_file(kind))


def char(key):
    """key = '<sid>' or '<sid>_h' -> SPR.chars['<key>_r'] meta (pictures written in game/assets/chars)"""
    sid = key.split('_')[0]; hat = key.endswith('_h'); src = f'{NSPR}/{sid}.swf'
    sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); heads = BC.head_ids(sw); rate = 60.0   # (the client plays every loaded clip at its own window's rate, 60: some sprite files declare 40 — the female Ecaflip 61, the female Sacrieur 111, the Roublard — and ran slowed down)
    anims = {a: ex[a] for a in RUNS if a in ex}
    jobs = [dict(key=a, sym=a, zoom=Z, frames=list(range(min(MAXF, tl.eff_frames(s))))) for a, s in anims.items()]
    R = {z: BC.render(src, jobs, f'{WORK}/chars/{key}', tl, z, hat, heads) for z in (0, 1, 2, 3)}
    items, frames = [], {}
    for job in jobs:
        a = job['key']; rb = R[0][a]; o = rb['meta']['origin']
        for n, fi in enumerate(job['frames'][:len(rb['imgs'])]):
            im = rb['imgs'][n]
            if im is None or not im.getbbox(): continue
            bb = im.getbbox(); b0 = np.asarray(im.crop(bb)).astype(np.int16); ch = []
            for z in (1, 2, 3):
                iz = R[z][a]['imgs'][n] if n < len(R[z][a]['imgs']) else None
                d = (np.asarray(iz.crop(bb)).astype(np.int16)[:, :, :3] - b0[:, :, :3]).mean(axis=2) if iz is not None else np.zeros(b0.shape[:2])
                ch.append(np.clip(d, 0, 255))
            items.append(((a, fi), im.crop(bb), Image.fromarray(np.stack(ch, axis=2).astype(np.uint8), 'RGB'))); frames[(a, fi)] = (o[0] - bb[0], o[1] - bb[1])
    atlas, pos = ST.pack([(k, b) for k, b, m in items], maxw=4096)
    atlas.save(f'{G}/assets/chars/{key}_r.webp', 'WEBP', quality=88, method=6)
    ma = Image.new('RGB', atlas.size)
    for k, b, m in items: ma.paste(m, pos[k][:2])
    ma.save(f'{G}/assets/chars/{key}_r_m.webp', 'WEBP', **BC.MASK_WEBP)   # (0.91: lossless masks)
    meta = dict(w=atlas.width, h=atlas.height, zoom=Z, anims={}); k = Z / 20.0
    for job in jobs:
        a = job['key']; F, A = [], []
        anc = tl.anchors(anims[a], frames=job['frames'])
        for n, fi in enumerate(job['frames']):
            if (a, fi) not in pos: continue
            x, y, w, h = pos[(a, fi)]; ox, oy = frames[(a, fi)]; F.append([x, y, w, h, round(ox, 2), round(oy, 2)])
            A.append([[SLOT[i], d, *[round(v * k, 4) for v in m[:4]], round(m[4] * k, 3), round(m[5] * k, 3), 1.0 if SLOT[i] == 1 else round(o_, 3)] for i, d, m, o_ in anc[n] if i in SLOT])
        meta['anims'][a] = dict(fps=rate, loop=True, f=F, anc=A)
    print(key + '_r', atlas.size, {a: len(v['f']) for a, v in meta['anims'].items()}, os.path.getsize(f'{G}/assets/chars/{key}_r.webp') // 1024, 'KB', flush=True)
    return meta


def chars(keys=None):
    SPR = json.load(open(f'{G}/data/sprites.json')); done = load_done('chars')
    keys = keys or sorted(k[:-2] for k in SPR['chars'] if k.endswith('_r'))
    for key in keys:
        if key in done: continue
        if not os.path.exists(f'{NSPR}/{key.split("_")[0]}.swf'): print('no new sprite', key); continue
        try: done[key] = char(key)
        except Exception as e: print('FAIL', key, e, flush=True); continue
        save_done('chars', done)
    return done


def walk_frames(tl, D, sid, lab):
    """frames of the nested walk clip shown at a label (the pet's own walk cycle)"""
    st = tl.states(sid); fi = lab
    if not st or fi >= len(st): return 24
    best = 1
    for e in st[fi].values():
        ch = e.get('char')
        if ch is not None and ch in D and D[ch].code == S.T_SPRITE: best = max(best, tl.eff_frames(ch))
    return best


def pets(syms=None):
    import build_acc060 as A6
    SPR = json.load(open(f'{G}/data/sprites.json')); C = json.load(open(f'{G}/data/content.json', encoding='utf-8'))
    seen = load_done('pets'); done = load_done('pets', merged=False)   # (skips what any part made; writes its own part)
    lib = f'{NEW}/clips/sprites/accessories'; where = {}
    for f in sorted(os.listdir(lib)):
        for k in S.exports(S.read_swf(f'{lib}/{f}')['tags']): where.setdefault(k, f'{lib}/{f}')
    syms = syms or [p['id'] for p in C['pets']]
    only = set(os.environ['MOVE_GROUPS'].split(',')) if os.environ.get('MOVE_GROUPS') else None   # (accessory files of this part: a3.swf,a4.swf…)
    groups = collections.defaultdict(list)
    for s in syms:
        if s in seen or s not in where or s not in SPR['acci']: continue
        if only and os.path.basename(where[s]) not in only: continue
        groups[where[s]].append(s)
    if os.environ.get('MOVE_LIST'): print({os.path.basename(k): len(v) for k, v in groups.items()}); return done
    for src, ss in groups.items():
        sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags']); rate = sw['rate']; jobs = {}
        for s in ss:
            labs = BA.frame_labels(D, ex[s])
            for v in ('R', 'L', 'F', 'B', 'S'):   # (the still views too, from the same client: one picture, one source)
                if v in labs: jobs[(s, v)] = dict(key=f'{s}__{v}', sym=s, snap=labs[v], zoom=Z, n=1)
            for v in ('WR', 'WL', 'WF', 'WB', 'WS'):
                if v in labs: jobs[(s, v)] = dict(key=f'{s}__{v}', sym=s, snap=labs[v], zoom=Z, n=min(MAXF, walk_frames(tl, D, ex[s], labs[v])))
        print(os.path.basename(src), len(ss), 'pets', len(jobs), 'walks', flush=True)
        r = ST.stage_render(src, list(jobs.values()), f'{WORK}/pets/{os.path.basename(src)[:-4]}', tagpatch=BC.make_patch(tl, None), prune=True)
        for s in ss:
            meta = SPR['acci'][s]; views, vf = {}, {}
            try: pic = Image.open(f'{G}/assets/acc/i/{s}.webp').convert('RGBA')
            except Exception: pic = None   # (a picture cut by an interrupted run: the new renders replace it)
            for v, fr in meta['f'].items():   # the still views: the new render, else the old picture
                if v.startswith('W'): continue
                rr = r.get(f'{s}__{v}'); fl = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if fl: views[v] = fl[:1]; continue
                if pic is None: continue
                fl = fr if isinstance(fr[0], list) else [fr]
                views[v] = [(pic.crop((x, y, x + w, y + h)), ox, oy) for x, y, w, h, ox, oy in fl]
            for v in ('WR', 'WL', 'WF', 'WB', 'WS'):
                rr = r.get(f'{s}__{v}')
                fl = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if len(fl) > 1: views[v] = fl; vf[v] = rate
                elif v in meta['f'] and pic is not None:   # (nothing new: the old walk stays)
                    fr = meta['f'][v]; fl0 = fr if isinstance(fr[0], list) else [fr]
                    views[v] = [(pic.crop((x, y, x + w, y + h)), ox, oy) for x, y, w, h, ox, oy in fl0]
                    if (meta.get('vf') or {}).get(v): vf[v] = meta['vf'][v]
            m2 = A6.write_item(s, views, zoom=meta.get('zoom') or Z, vf=vf or None)
            if meta.get('m'): m2['m'] = 1   # (no pet takes the character's colours; kept if one did)
            done[s] = m2; print('pet', s, {v: len(x) for v, x in views.items() if v.startswith('W')}, flush=True)
        save_done('pets', done)
    return done


BOSSES = ('dark_vlad', 'goultard', 'qutan')


def bosses():
    """'<sprite>_w60': walkR / walkL of the humanoid bosses at 60 fps, at their sheet's zoom (patch_060 sets
    C.bosses[id].walk60, render.js drawMob takes the walks from it)"""
    SPR = json.load(open(f'{G}/data/sprites.json')); C = json.load(open(f'{G}/data/content.json', encoding='utf-8')); done = load_done('bosses')
    for bid in BOSSES:
        key = C['bosses'][bid]['sprite']; gfx = key.split('_')[0].rstrip('r'); src = f'{NSPR}/{gfx}.swf'
        if key + '_w60' in done or not os.path.exists(src): continue
        sw = S.read_swf(src); ex = S.exports(sw['tags']); tl = TL.Timeline(sw); zoom = SPR['mobs'][key]['zoom']
        jobs = [dict(key=a, sym=a, zoom=zoom, n=min(MAXF, tl.eff_frames(ex[a]))) for a in ('walkR', 'walkL') if a in ex]
        res = ST.stage_render(src, jobs, f'{WORK}/bosses/{key}', prune=True); items, frames = [], {}
        for job in jobs:
            r = res[job['key']]; fl = []
            for i, im in enumerate(r['imgs']):
                if im is None or not im.getbbox(): fl.append(None); continue
                c, ox, oy = ST.crop(im, r['meta']['origin']); items.append(((job['key'], i), c)); fl.append((round(ox, 2), round(oy, 2)))
            frames[job['key']] = fl
        atlas, pos = ST.pack(items, maxw=4096)
        atlas.save(f'{G}/assets/mobs/{key}_w60.webp', 'WEBP', quality=88, method=6)
        anims = {}
        for a, fl in frames.items():
            F = []
            for i, o in enumerate(fl):
                if o is None: F.append(F[-1] if F else [0, 0, 1, 1, 0, 0]); continue
                x, y, w, h = pos[(a, i)]; F.append([x, y, w, h, o[0], o[1]])
            anims[a] = dict(fps=sw['rate'], f=F)
        done[key + '_w60'] = dict(w=atlas.width, h=atlas.height, zoom=zoom, anims=anims); save_done('bosses', done)
        print(key + '_w60', atlas.size, {a: len(v['f']) for a, v in anims.items()}, flush=True)
    return done


def apply(only=None):
    import sprio
    ch, pe, bo = load_done('chars'), load_done('pets'), load_done('bosses')
    if only is not None:   # (0.91: keys given: only those are written; the cache's older sheets lack the later front layers / fps)
        ch = {k: v for k, v in ch.items() if k in only[0]}; pe = {k: v for k, v in pe.items() if k in only[1]}; bo = {} if only[0] or only[1] else bo
    def upd(S_):
        for key, meta in ch.items(): S_['chars'][key + '_r'] = meta
        for s, meta in pe.items(): S_['acci'][s] = meta
        for k, meta in bo.items(): S_['mobs'][k] = meta
    sprio.update(upd); print('sprites.json:', len(ch), 'run sheets,', len(pe), 'pets,', len(bo), 'boss walks')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'; rest = sys.argv[2:] or None
    if what in ('chars', 'all'): chars(rest if what == 'chars' else None)
    if what in ('pets', 'all'): pets(rest if what == 'pets' else None)
    if what in ('bosses', 'all'): bosses()
    if what in ('apply', 'all', 'chars', 'pets', 'bosses'): apply(None if not rest else (rest if what == 'chars' else [], rest if what == 'pets' else []))
