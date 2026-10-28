"""0.94 (running seen from the back, the shield showed its face over the character's back for a moment, on nearly
every class — only the male Sadida keeps that moment): in the back runs (`runL`) of every character sheet but the male
Sadida's (100), a frame's shield anchor in the front view (R) — drawn over the whole character, CharSprite.draw — is
dropped when the frame also has the back view (L); a frame with the front view only (Xélor, Eniripsa, female Sacrieur)
takes the back view of the nearest frame that has one instead (the shield stays behind, no blink).
Idempotent; shield_anc092.py calls fix() too, so a rebuild of the anchors keeps it.
usage: python tools/assets/shield_back094.py [--dry]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import sys, json, copy

KEEP = {'100'}   # (the male Sadida: his back run shows the shield's face)
ANIMS = ('runL',)


def fix(chars):
    st = dict(sheets=0, dropped=0, borrowed=0)
    for key, c in chars.items():
        if key.split('_')[0] in KEEP: continue
        for an_name in ANIMS:
            an = (c.get('anims') or {}).get(an_name)
            if not an or not an.get('anc'): continue
            anc = an['anc']; n = len(anc); hit = False
            views = [[a[1] for a in (fr or []) if a[0] == 4] for fr in anc]
            for i, fr in enumerate(anc):
                if not fr or 'R' not in views[i]: continue
                if 'L' in views[i]:
                    fr[:] = [a for a in fr if not (a[0] == 4 and a[1] == 'R')]; st['dropped'] += 1; hit = True
                else:
                    js = sorted((j for j in range(n) if 'L' in views[j]), key=lambda j: min(abs(j - i), n - abs(j - i)))
                    if not js: continue
                    L = [copy.deepcopy(a) for a in anc[js[0]] if a[0] == 4 and a[1] == 'L']
                    fr[:] = [a for a in fr if a[0] != 4] + L; st['borrowed'] += 1; hit = True
            st['sheets'] += hit
    return st


if __name__ == '__main__':
    import sprio
    if '--dry' in sys.argv:
        print(fix(json.load(open(sprio.P))['chars']))
    else:
        out = {}
        sprio.update(lambda S: out.update(fix(S['chars'])))
        print(out)
