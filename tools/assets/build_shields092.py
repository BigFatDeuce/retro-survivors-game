"""0.92: the Dofus shields as a skin slot — their worn pictures and shop pictures, as build_acc060 `new` does for
the hats / capes / pets: every shield look (item type 82, symbol 82_<gfx>) of the up-to-date client that has an item,
rendered at zoom 4.8 from its client symbol, views R and L (the shield holders only use those), still (first frame of the
view) -> game/assets/acc/i/<sym>.webp + SPR.acci[sym]; shop pictures it_82_<gfx> (180 px) into icons3 (build_icons20).
The list (sym, gfx, level = the highest of its items, item, names in 7 languages = the highest-level item's: the shield
itself rather than its 'broken' low-level copy) -> work/shields092.json, read by tools/content/patch_091.py.
usage: python tools/assets/build_shields092.py [sym…]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, collections
import swflib as S, timeline as TL, stage as ST
import build_chars20 as BC, build_acc060 as B6

LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')


def shield_list():
    I = {lg: json.load(open(f'{ROOT}/work/lang_new/items_{lg}.json', encoding='utf-8'))['I']['u'] for lg in LG}
    by = collections.defaultdict(list)
    for iid, v in I['fr'].items():
        if v.get('t') == 82: by[f"82_{v['g']}"].append((v.get('l', 1), -len(v.get('n', '')), int(iid)))
    out = []
    for sym, lst in by.items():
        lvl, _, iid = max(lst)   # (the highest level; same level: the shortest name, not the 'broken' one)
        name = {lg: (I[lg].get(str(iid)) or {}).get('n') or I['fr'][str(iid)]['n'] for lg in LG}
        out.append(dict(sym=sym, gfx=int(sym.split('_')[1]), lvl=lvl, item=iid, name=name))
    return sorted(out, key=lambda e: e['gfx'])


def run(only=None):
    lib = f'{B6.NEW}/clips/sprites/accessories'; where = {}
    for f in sorted(os.listdir(lib)):
        sw = S.read_swf(f'{lib}/{f}')
        for k in S.exports(sw['tags']): where.setdefault(k, f'{lib}/{f}')
    lst = [e for e in shield_list() if e['sym'] in where and (not only or e['sym'] in only)]
    groups = collections.defaultdict(list)
    for e in lst: groups[where[e['sym']]].append(e)
    acci, done = {}, []
    for src, es in groups.items():
        sw = S.read_swf(src); tl = TL.Timeline(sw); ex = S.exports(sw['tags']); D = S.defs(sw['tags']); jobs = []
        for e in es:
            labs = B6.frame_labels(D, ex[e['sym']]); e['views'] = [v for v in ('R', 'L') if v in labs]
            for v in e['views']: jobs.append(dict(key=f"{e['sym']}__{v}", sym=e['sym'], snap=labs[v], zoom=B6.Z, n=1))
        print(os.path.basename(src), len(es), 'shields,', len(jobs), 'views', flush=True)
        r = ST.stage_render(src, jobs, f'{ROOT}/work/shields092/{os.path.basename(src)[:-4]}', tagpatch=BC.make_patch(tl, None), prune=True, margin_px=int(os.environ.get('MARGIN', 30)))
        for e in es:
            views = {}
            for v in e['views']:
                rr = r.get(f"{e['sym']}__{v}"); fr = [ST.crop(im, rr['meta']['origin']) for im in (rr['imgs'] if rr else []) if im is not None and im.getbbox()]
                if fr: views[v] = fr[:1]
            if 'R' not in views: print('empty', e['sym'], e['name']['fr']); continue
            if 'L' not in views: views['L'] = views['R']
            acci[e['sym']] = B6.write_item(e['sym'], views); done.append(e)
    import sprio
    sprio.update(lambda S_: S_.setdefault('acci', {}).update(acci))
    import build_icons20 as BI
    BI.RAW = f'{B6.NEW}/clips/items'
    ims = BI.render([f"it_82_{e['gfx']}" for e in done], work=f'{ROOT}/work/shields092/icons')
    if ims: BI.merge(ims)
    old = {e['sym']: e for e in json.load(open(f'{ROOT}/work/shields092.json', encoding='utf-8'))} if only and os.path.exists(f'{ROOT}/work/shields092.json') else {}
    old.update({e['sym']: {k: e[k] for k in ('sym', 'gfx', 'lvl', 'item', 'name')} for e in done})
    json.dump(sorted(old.values(), key=lambda e: e['gfx']), open(f'{ROOT}/work/shields092.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('shields', len(done), 'rendered,', len(ims), 'icons')


if __name__ == '__main__':
    run(set(sys.argv[1:]) or None)
