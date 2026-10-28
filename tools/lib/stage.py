"""Render SWF symbols to PNG frames with FFDec (JPEXS), at any zoom, on a transparent stage.

For every job a small SWF is written: all the definitions of the source file plus a main timeline that places the
target symbol (scaled by the zoom, registration point snapped to a whole pixel) and shows as many frames as needed
(nested clips advance one frame per main frame, like in the player). One JVM renders a whole batch of such files.

job = dict(key, cid=<id> | sym=<export name> | root=True, zoom, frames=[...] | n=<count>, cx=<color transform>)
result = {key: {'imgs': [PIL RGBA per frame], 'meta': {'origin': (ox, oy), 'zoom': z}}}
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import os, sys, json, math, shutil, struct, subprocess, glob
import swflib as S, timeline as TL
from PIL import Image

FFDEC = f'{ROOT}/ffdec/ffdec-cli.jar'
CTRL = {S.T_SHOWFRAME, S.T_PLACE, S.T_PLACE2, S.T_PLACE3, S.T_REMOVE, S.T_REMOVE2, S.T_DOACTION, S.T_FRAMELABEL, 9}
ROOT_ID = 59999


def make_sprite(sid, sub):
    t = S.Tag(S.T_SPRITE, struct.pack('<HH', sid, sum(1 for x in sub if x.code == S.T_SHOWFRAME)), sub=list(sub))
    return t


def root_sprite(sw, sid=ROOT_ID):
    sub = [t for t in sw['tags'] if t.code in CTRL and t.code != 9]
    if not any(t.code == S.T_SHOWFRAME for t in sub): sub.append(S.Tag(S.T_SHOWFRAME, b''))
    return make_sprite(sid, sub)


def truncate(t):
    """a sprite reduced to its first frame (frozen clip)"""
    sub = []
    for x in t.sub:
        if x.code == S.T_DOACTION: continue
        sub.append(x)
        if x.code == S.T_SHOWFRAME: break
    return make_sprite(t.sprite_id, sub)


def _target(sw, job):
    if job.get('root'):
        if not any(t.code == S.T_SPRITE and t.sprite_id == ROOT_ID for t in sw['tags']):
            sw['tags'].append(root_sprite(sw))
        return ROOT_ID
    if 'cid' in job: return job['cid']
    return S.exports(sw['tags'])[job['sym']]


def hold(t, n, pad=600):
    """a sprite that stops on its frame n (a stop() action): the frames after it are dropped, the last one is held"""
    sub = []; fi = 0
    for x in t.sub:
        if x.code == S.T_DOACTION: continue
        sub.append(x)
        if x.code == S.T_SHOWFRAME:
            if fi == n: break
            fi += 1
    sub += [S.Tag(S.T_SHOWFRAME, b'') for _ in range(pad)]
    return make_sprite(t.sprite_id, sub)


def stops_of(sw):
    """{sprite id: frame index} of every stop() on a frame other than the first"""
    out = {}
    for t in sw['tags']:
        if t.code != S.T_SPRITE: continue
        for fi, bodies in S.scripts_of(t.sub).items():
            if fi > 0 and any(('op', 'stop') in S.action_strings(b) for b in bodies): out.setdefault(t.sprite_id, fi)
    return out


def prepare(src, jobs, workdir, freeze=False, margin_px=2, tag='', holds=None, tagpatch=None, prune=False):
    """writes one SWF per job into workdir/in; returns [(file stem, job, frames, origin)]"""
    sw = S.read_swf(src)
    if holds is True: holds = stops_of(sw)
    os.makedirs(f'{workdir}/in', exist_ok=True)
    out = []
    targets = [_target(sw, j) for j in jobs]
    frozen = set()
    if freeze is True:
        tl0 = TL.Timeline(sw); frozen = set(tl0.stop1)
    elif freeze: frozen = set(freeze)
    tags = []
    for t in sw['tags']:
        if t.code in CTRL or t.code == 9: continue
        if tagpatch: t = tagpatch(t)
        if t.code == S.T_SPRITE and t.sprite_id in frozen: t = truncate(t)
        elif t.code == S.T_SPRITE and holds and t.sprite_id in holds: t = hold(t, holds[t.sprite_id])
        tags.append(t)
    def pruned(roots):   # only what a symbol needs (much smaller files, much faster renders)
        need = S.deps(tags, set(roots)); fontish = need & {k for k, v in S.defs(tags).items() if v.code in S.FONT_CODES}
        return [t for t in tags if (t.cid is None and t.code not in (S.T_EXPORT, 57, 71) and (t.code not in (13, 62, 73, 88) or fontish)) or (t.cid is not None and t.cid in need)]
    tl = TL.Timeline(dict(sw, tags=tags), frozen=frozen)
    extra = []
    for k, (job, tid) in enumerate(zip(jobs, targets)):
        if job.get('snap') is not None:
            # the clip shown on one frame (a label: R, L…), its children still playing: a one-frame wrapper of that display list
            lst = tl.states(tid)[min(job['snap'], len(tl.states(tid)) - 1)]; sub = []
            for d in sorted(lst):
                e = lst[d]
                sub.append(S.make_place2(d, char=e['char'], matrix=e['m'], cx=e.get('cx'), name=e.get('name'), clipdepth=e.get('clip')))
            sub.append(S.Tag(S.T_SHOWFRAME, b''))
            w = make_sprite(61000 + k, sub); extra.append(w); targets[k] = 61000 + k
    if extra:
        tags = tags + extra; tl = TL.Timeline(dict(sw, tags=tags), frozen=frozen)
    for job, tid in zip(jobs, targets):
        try:
            n = job.get('n') or tl.eff_frames(tid)
            frames = list(job.get('frames') if job.get('frames') is not None else range(n))
            b = tuple(job['bounds']) if job.get('bounds') else tl.bounds(tid, frames=frames)   # 'bounds' (twips): render only that box
        except KeyError as e:   # 0.32: an export pointing to a character the file doesn't define (o3.swf '1032'): skip that one only
            print('missing character', e, 'for', job.get('key'), flush=True); out.append((None, job, [], None)); continue
        if b[0] > b[1]: out.append((None, job, frames, None)); continue
        z = float(job.get('zoom', 1.0)); k = z / 20.0   # px per twip
        L = job.get('mat')   # an extra local transform [a, b, c, d] (rotation, scale, flip) baked into the render
        if L: b = tl.bounds(tid, frames=frames, m=[L[0], L[1], L[2], L[3], 0.0, 0.0])
        ox = math.ceil(-b[0] * k + margin_px); oy = math.ceil(-b[2] * k + margin_px)
        W = math.ceil((b[1] - b[0]) * k + 2 * margin_px + 1); H = math.ceil((b[3] - b[2]) * k + 2 * margin_px + 1)
        m = [z, 0.0, 0.0, z, ox * 20.0, oy * 20.0] if not L else [z * L[0], z * L[1], z * L[2], z * L[3], ox * 20.0, oy * 20.0]
        main = [S.make_place2(1, char=tid, matrix=m, cx=job.get('cx'))]
        main += [S.Tag(S.T_SHOWFRAME, b'') for _ in range(max(frames) + 1)]
        stem = f'{tag}{job["key"]}'.replace('/', '_')
        jt = pruned([tid]) if prune else tags
        S.write_swf(dict(version=max(8, sw['version']), rect=(0, W * 20, 0, H * 20), rate=sw['rate'], tags=jt + main), f'{workdir}/in/{stem}.swf')
        out.append((stem, job, frames, (ox, oy)))
    return out


def run_ffdec(workdir, timeout=3600):
    outd = f'{workdir}/out'
    if os.path.exists(outd): shutil.rmtree(outd)
    cmd = ['java', '-Xmx3g', '-Djava.awt.headless=true', '-jar', FFDEC, '-onerror', 'ignore', '-format', 'frame:png', '-ignorebackground',
           '-export', 'frame', outd, f'{workdir}/in']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return outd


def collect(outd, stem, frames):
    d = None
    for cand in (f'{outd}/{stem}.swf', f'{outd}/{stem}/frames', f'{outd}/{stem}'):
        if os.path.isdir(cand) and glob.glob(f'{cand}/*.png'): d = cand; break
    if d is None: return [None] * len(frames)
    imgs = []
    for f in frames:
        p = f'{d}/{f + 1}.png'
        imgs.append(Image.open(p).convert('RGBA') if os.path.exists(p) else None)
    return imgs


def stage_batch(items, workdir, freeze=False, margin_px=2, holds=None, tagpatch=None, prune=False):
    """items: [(src, jobs)] -> {key: {'imgs', 'meta'}} (one FFDec run for everything)"""
    if os.path.exists(f'{workdir}/in'): shutil.rmtree(f'{workdir}/in')
    plan = []
    for i, (src, jobs) in enumerate(items):
        try: plan += prepare(src, jobs, workdir, freeze, margin_px, tag=f'{i}_', holds=holds, tagpatch=tagpatch, prune=prune)
        except Exception as e:
            print('prepare fail', src, e, flush=True)
            plan += [(None, j, [], 'error') for j in jobs]
    outd = run_ffdec(workdir)
    res = {}
    for stem, job, frames, origin in plan:
        imgs = collect(outd, stem, frames) if stem else []
        res[job['key']] = dict(imgs=imgs, meta=dict(origin=None if origin == 'error' else origin, zoom=job.get('zoom', 1.0), error=origin == 'error'))
    return res


def stage_render(src, jobs, workdir, mode=None, freeze=False, margin_px=2, holds=None, tagpatch=None, prune=False):
    return stage_batch([(src, jobs)], workdir, freeze, margin_px, holds, tagpatch, prune)


def crop(im, origin):
    bb = im.getbbox()
    if not bb: return None, 0, 0
    return im.crop(bb), origin[0] - bb[0], origin[1] - bb[1]


def pack(items, maxw=4096, pad=2):
    """shelf packing of [(key, img)] sorted by height -> (atlas, {key: (x, y, w, h)})"""
    items = sorted(items, key=lambda e: (-e[1].height, -e[1].width))
    x = y = 0; rowh = 0; pos = {}; W = 0
    for k, im in items:
        w, h = im.size
        if x + w + pad > maxw and x > 0:
            y += rowh + pad; x = 0; rowh = 0
        pos[k] = (x, y, w, h); x += w + pad; rowh = max(rowh, h); W = max(W, x - pad)
    H = y + rowh
    atlas = Image.new('RGBA', (max(1, W), max(1, H)))
    for k, im in items:
        atlas.paste(im, pos[k][:2])
    return atlas, pos
