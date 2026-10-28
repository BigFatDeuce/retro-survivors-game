"""0.95 (announcements more mature, close to the logo): the announcement font game/assets/fonts/cinzel.woff2 from
Cinzel (OFL, https://github.com/google/fonts/tree/main/ofl/cinzel — its OFL.txt is game/assets/fonts/CINZEL_LICENSE.txt):
the variable font's weight axis cut to 700-900 (juice.js annFont uses 900, banners 700) and the Latin subset the 7 game
languages need, plus typographic punctuation (… ’ « » – —). ~40 KB.
usage: python tools/assets/build_cinzel095.py <Cinzel[wght].ttf>"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import io, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

UNI = list(range(0x20, 0x7F)) + list(range(0xA0, 0x180)) + [0x152, 0x153, 0x178, 0x2C6, 0x2DC] + list(range(0x2013, 0x2027)) + [0x2030, 0x2039, 0x203A, 0x20AC, 0x2122]

if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(__doc__)
    f = instancer.instantiateVariableFont(TTFont(sys.argv[1]), {'wght': (700, 900)})
    b = io.BytesIO(); f.save(b); b.seek(0); f = TTFont(b)   # (reloaded: the subsetter trips on the instancer's lazy gvar)
    opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']; opts.name_IDs = ['*']; opts.notdef_outline = True
    s = subset.Subsetter(opts); s.populate(unicodes=UNI); s.subset(f)
    out = f'{ROOT}/game/assets/fonts/cinzel.woff2'; f.flavor = 'woff2'; f.save(out)
    print(out, len(f.getGlyphOrder()), 'glyphs')
