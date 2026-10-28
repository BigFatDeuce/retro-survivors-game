"""Official Dofus Retro translations (lang files of the 7 client languages) -> per-language name dicts."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json, os, re
LANGS = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
D = f'{ROOT}/work/lang_json'
_c = {}

def _load(kind, lg):
    k = (kind, lg)
    if k not in _c:
        p = f'{D}/{kind}_{lg}.json'
        _c[k] = json.load(open(p)) if os.path.exists(p) else {}
    return _c[k]

def _clean(s):
    if not isinstance(s, str): return None
    s = s.strip()
    if not s or s.startswith('[wait') or s.startswith('//') or s.startswith('#'): return None
    return s

def _pick(get):
    out = {}
    for lg in LANGS:
        try: v = _clean(get(lg))
        except Exception: v = None
        if v: out[lg] = v
    for lg in LANGS:  # fallbacks: en, then fr
        if lg not in out:
            out[lg] = out.get('en') or out.get('fr') or ''
    return out

def spell(sid): return _pick(lambda lg: _load('spells', lg)['S'][str(sid)]['n'])
def spell_desc(sid): return _pick(lambda lg: _load('spells', lg)['S'][str(sid)]['d'])
def monster(did): return _pick(lambda lg: _load('monsters', lg)['M'][str(did)]['n'])
def item(iid): return _pick(lambda lg: _load('items', lg)['I']['u'][str(iid)]['n'])
def item_type(t): return _pick(lambda lg: _load('items', lg)['I']['t'][str(t)]['n'])
def breed(b): return _pick(lambda lg: _load('classes', lg)['G'][str(b)]['sn'])
def subarea(sa): return _pick(lambda lg: _load('maps', lg)['MA']['sa'][str(sa)]['n'])
def area(a): return _pick(lambda lg: _load('maps', lg)['MA']['a'][str(a)]['n'])
def ui(key): return _pick(lambda lg: _load('lang', lg)[key])

def item_info(iid): return _load('items', 'fr')['I']['u'].get(str(iid))

_fr_spell_ids = None
def spell_by_fr_name(name):
    """Find an official spell id from its French name (first, lowest id)."""
    global _fr_spell_ids
    if _fr_spell_ids is None:
        _fr_spell_ids = {}
        for k, v in sorted(_load('spells', 'fr')['S'].items(), key=lambda kv: int(kv[0])):
            n = _clean(v.get('n'))
            if n: _fr_spell_ids.setdefault(n.lower(), int(k))
    return _fr_spell_ids.get(name.lower().strip())

def find_items(pred):
    return [(int(k), v) for k, v in _load('items', 'fr')['I']['u'].items() if pred(v)]

def hints(lg, n=60):
    """Official loading hints (lang file 'hints')."""
    d = _load('hints', lg)
    out = []
    for k, v in sorted((d.get('HI') or {}).items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
        t = v.get('d') if isinstance(v, dict) else v
        t = _clean(t)
        if t: out.append(re.sub(r'<[^>]+>', '', t))
    return out[:n]
