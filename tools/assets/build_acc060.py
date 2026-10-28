"""0.60: one small picture per accessory (hat, cape, pet, weapon look) instead of 14 big sheets.
The big sheets (acc, acc_1 … acc12, ~30 MB once decoded each) were decoded then cut at the start of a run: micro-freezes.
Now game/assets/acc/i/<sym>.webp holds every view of one accessory (+ <sym>_m.webp, the colour mask of the few hats that
take the character's colours, laid out like the picture), described in sprites.json SPR.acci[sym] = {w, h, zoom, fps,
f: {view: frame | [frames]}, vf: {view: fps}, m: 1}; a run loads only what it wears.
  new [sym…]       the hats / capes / pets of the up-to-date client (RS_NEWCLIENT, default %LOCALAPPDATA%/Ankama/Retro/
                   resources/app/retroclient) that the game does not have, rendered at zoom 4.8 straight from their client
                   symbols (R L F B S for hats, R L RR RL for capes, R L F B S + walks WR WL (24 frames) WF WB WS (12) for
                   pets), + their shop pictures (it_<t>_<g>, 180 px) in icons3. Writes work/newskins060.json (the list)
  weapons sym…     weapon looks (R / L) of the 1.41.9 client + their shop pictures
  icons            the shop pictures of the accessories rendered by 'new'
(0.60 also had 'split': the one-time move of the old sheets into these pictures, done and removed.)
usage: python tools/assets/build_acc060.py new [sym…] | weapons sym… | icons"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, collections
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC
import numpy as np
from PIL import Image

G = f'{ROOT}/game'
OUTD = f'{G}/assets/acc/i'
from _root import CLIENT as NEW   # the up-to-date installed client (_root.py)
Z = 4.8
VIEWS = {'16': ['R', 'L', 'F', 'B', 'S'], '17': ['R', 'L', 'RR', 'RL'], '18': ['R', 'L', 'F', 'B', 'S', 'WR', 'WL', 'WF', 'WB', 'WS']}
NFR = {'WR': 24, 'WL': 24, 'WF': 12, 'WB': 12, 'WS': 12}
Q = 95
METHOD = int(os.environ.get('ACC_WEBP_METHOD', '6'))   # (0.60: 4 encodes the 60 fps pet walks several times faster)


# the client's accessory libraries (raw/rc, the 1.41.9 client) and the helpers the accessory tools share (they were in
# build_acc20.py, the v2.0 sheet builder, retired with its acc / acc2 / accm sheets in 0.60)
ACC_LIB = f'{ROOT}/raw/rc/clips/sprites/accessories'
SRCS = [f'{ACC_LIB}/{n}.swf' for n in ('a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'accessories_autres', 'accessories')]


def frame_labels(defs, sid):
    t = defs[sid]; fi = 0; out = {}
    for x in t.sub:
        if x.code == S.T_FRAMELABEL: out.setdefault(x.data.split(b'\0')[0].decode('latin1'), fi)
        if x.code == S.T_SHOWFRAME: fi += 1
    return out


def libs():
    L = {}
    for p in SRCS:
        sw = S.read_swf(p); ex = S.exports(sw['tags'])
        for k in ex: L.setdefault(k, p)
    return L


def crops(r):
    out = []
    for im in r['imgs']:
        if im is None or not im.getbbox(): out.append(None); continue
        c, ox, oy = ST.crop(im, r['meta']['origin']); out.append((c, ox, oy))
    return out


def best_match(ref, ox, oy, cands, tol=3):
    best = None; h, w = ref.shape[:2]
    for i, cd in enumerate(cands):
        if cd is None: continue
        c, cx_, cy_ = cd
        if abs(c.width - w) > tol or abs(c.height - h) > tol or abs(cx_ - ox) > tol or abs(cy_ - oy) > tol: continue
        dx, dy = round(cx_ - ox), round(cy_ - oy); src = np.asarray(c).astype(np.int16); cc = np.zeros_like(ref)
        ys0, xs0 = max(0, dy), max(0, dx); hh, ww = min(h, src.shape[0] - ys0), min(w, src.shape[1] - xs0)
        if hh <= 0 or ww <= 0: continue
        cc[:hh, :ww] = src[ys0:ys0 + hh, xs0:xs0 + ww]
        err = np.abs(cc - ref).mean()
        if best is None or err < best[0]: best = (err, i)
    return best


def render(src, jobs, wd, tl, zone):
    """the Le Oiram cap (16_7) keeps the bolder white lines of its 'M' (build_icons20.LINEPATCH), rendered on its own"""
    import build_icons20 as BI
    zp = BC.make_patch(tl, zone)
    oiram = [j for j in jobs if 'it_' + j['sym'] in BI.LINEPATCH]
    rest = [j for j in jobs if j not in oiram]
    out = ST.stage_render(src, rest, wd, tagpatch=zp, prune=True) if rest else {}
    for j in oiram:
        sp = BI.shape_patch(BI.LINEPATCH['it_' + j['sym']])
        out.update(ST.stage_render(src, [j], wd + '_oiram', tagpatch=lambda t: sp(zp(t)), prune=True))
    return out


def write_item(sym, views, masks=None, zoom=Z, vf=None):
    """views: {view: [(img, ox, oy)…]} -> the picture (+ mask laid out the same) and its frames"""
    os.makedirs(OUTD, exist_ok=True)
    items = [((v, i), im) for v, fl in views.items() for i, (im, ox, oy) in enumerate(fl)]
    atlas, pos = ST.pack(items, maxw=2048)
    atlas.save(f'{OUTD}/{sym}.webp', 'WEBP', quality=Q, method=METHOD)
    f = {}
    for v, fl in views.items():
        fr = [[*pos[(v, i)], round(ox, 2), round(oy, 2)] for i, (im, ox, oy) in enumerate(fl)]
        f[v] = fr if len(fl) > 1 else fr[0]
    meta = dict(w=atlas.width, h=atlas.height, zoom=zoom, f=f)
    if vf: meta['vf'] = vf
    if masks:
        m = Image.new('RGBA', atlas.size)
        for v, mim in masks.items():
            if (v, 0) not in pos: continue
            x, y, w, h = pos[(v, 0)]; m.paste(mim.resize((w, h), Image.LANCZOS), (x, y))
        m.save(f'{OUTD}/{sym}_m.webp', 'WEBP', quality=Q, method=METHOD); meta['m'] = 1
    return meta


def new_list():
    """the new client's skins the game does not have: [{sym, type, gfx, lvl, item, name{7}}]"""
    C = json.load(open(f'{G}/data/content.json', encoding='utf-8'))
    have = {it['id'] for k in ('hats', 'capes', 'pets') for it in C[k]}
    LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
    I = {lg: json.load(open(f'{ROOT}/work/lang_new/items_{lg}.json', encoding='utf-8'))['I']['u'] for lg in LG}
    by = collections.defaultdict(list)
    for iid, v in I['fr'].items():
        if v.get('t') in (16, 17, 18): by[f"{v['t']}_{v['g']}"].append((v.get('l', 1), int(iid)))
    out = []
    for sym, lst in by.items():
        if sym in have: continue
        lvl, iid = min(lst)   # (one entry per look: the lowest level item wearing it)
        name = {lg: (I[lg].get(str(iid)) or {}).get('n') or I['fr'][str(iid)]['n'] for lg in LG}
        out.append(dict(sym=sym, type=sym.split('_')[0], gfx=int(sym.split('_')[1]), lvl=lvl, item=iid, name=name))
    return out


def render_new(only=None):
    lib = f'{NEW}/clips/sprites/accessories'; where = {}
    for f in sorted(os.listdir(lib)):
        sw = S.read_swf(f'{lib}/{f}')
        for k in S.exports(sw['tags']): where.setdefault(k, f'{lib}/{f}')
    lst = [e for e in new_list() if e['sym'] in where and (not only or e['sym'] in only)]
    acci = {}; groups = collections.defaultdict(list)
    for e in lst: groups[where[e['sym']]].append(e)
    done = []
    for src, es in groups.items():
        sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags']); jobs = []
        for e in es:
            labs = frame_labels(D, ex[e['sym']]); want = [v for v in VIEWS[e['type']] if v in labs]
            if 'R' not in want or 'L' not in want: print('skip (no R / L view)', e['sym'], e['name']['fr']); continue
            for v in want: jobs.append(dict(key=f"{e['sym']}__{v}", sym=e['sym'], snap=labs[v], zoom=Z, n=NFR.get(v, 1)))   # (no '|': render file names on Windows)
            e['views'] = want
        print(os.path.basename(src), len(es), 'accessories,', len(jobs), 'views', flush=True)
        r = ST.stage_render(src, jobs, f'{ROOT}/work/acc060/{os.path.basename(src)[:-4]}', tagpatch=BC.make_patch(tl, None), prune=True)
        for e in es:
            if 'views' not in e: continue
            views, vf = {}, {}
            for v in e['views']:
                rr = r.get(f"{e['sym']}__{v}")
                fr = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if fr: views[v] = fr if NFR.get(v, 1) > 1 else fr[:1]
                if len(views.get(v, [])) > 1: vf[v] = 20   # (as the 0.29-0.41 walks: sheets at 20 fps)
            if 'R' not in views: print('empty', e['sym']); continue
            acci[e['sym']] = write_item(e['sym'], views, None, vf=vf or None); done.append(e)
    import sprio
    sprio.update(lambda S_: S_.setdefault('acci', {}).update(acci))
    icons_new(done)


def icons_new(done=None):
    """the new skins' shop pictures (HD, 180 px) from the new client's item clips + work/newskins060.json"""
    if done is None:   # (only the pictures: the skins already rendered into SPR.acci)
        A = json.load(open(f'{G}/data/sprites.json'))['acci']; done = [e for e in new_list() if e['sym'] in A]
    import build_icons20 as BI
    BI.RAW = f'{NEW}/clips/items'
    ims = BI.render([f"it_{e['type']}_{e['gfx']}" for e in done], work=f'{ROOT}/work/acc060/icons')
    if ims: BI.merge(ims)   # (never re-encode the icon pages for nothing)
    json.dump([{k: e[k] for k in ('sym', 'type', 'gfx', 'lvl', 'item', 'name')} for e in done], open(f'{ROOT}/work/newskins060.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('new', len(done), 'accessories,', len(ims), 'icons')


def render_weapons(syms):
    """weapon looks (R / L views, still) of the 1.41.9 client (raw/rc accessories) + their shop pictures"""
    L = libs(); acci = {}; groups = collections.defaultdict(list)
    for sym in syms: groups[L[sym]].append(sym)
    for src, ss in groups.items():
        sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags']); jobs = []
        for sym in ss:
            labs = frame_labels(D, ex[sym])
            for v in ('R', 'L'):
                if v in labs: jobs.append(dict(key=f'{sym}__{v}', sym=sym, snap=labs[v], zoom=Z, n=1))
        r = ST.stage_render(src, jobs, f'{ROOT}/work/acc060w/{os.path.basename(src)[:-4]}', tagpatch=BC.make_patch(tl, None), prune=True, margin_px=int(os.environ.get('MARGIN', 2)))   # (0.68: MARGIN=60, the Toh'Lo hammer's horns went past its declared bounds)
        for sym in ss:
            views = {}
            for v in ('R', 'L'):
                rr = r.get(f'{sym}__{v}'); fr = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if fr: views[v] = fr[:1]
            if 'R' in views: acci[sym] = write_item(sym, views); print('weapon', sym, list(views))
    import sprio
    sprio.update(lambda S_: S_.setdefault('acci', {}).update(acci))
    import build_icons20 as BI
    ims = BI.render([f'it_{s}' for s in acci], work=f'{ROOT}/work/acc060w/icons')
    if ims: BI.merge(ims)
    print('weapons', len(acci), 'looks,', len(ims), 'icons')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('new', 'weapons', 'icons'): sys.exit(__doc__)
    if sys.argv[1] == 'new': render_new(set(sys.argv[2:]) or None)
    elif sys.argv[1] == 'weapons': render_weapons(sys.argv[2:])
    elif sys.argv[1] == 'icons': icons_new()
