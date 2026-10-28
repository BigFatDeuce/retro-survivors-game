"""0.85 (damage numbers as the client draws them): the client's own glyphs of its damage numbers — the Verdana Bold
embedded in clips/points/1/0.swf (DefineFont3), exported by FFDec as TTF — cut down to the characters numbers use and
saved as game/assets/fonts/retronum.woff2 (font 'RetroNum'; no name / metadata kept beyond what a font needs).
usage: python tools/assets/build_retronum085.py <exported.ttf>   (java -jar ffdec/ffdec.jar -format font:ttf -export font <dir>
       <retroclient>/clips/points/1/0.swf)"""
import sys, os
from fontTools.ttLib import TTFont
from fontTools import subset
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT

src = sys.argv[1]
f = TTFont(src)
opt = subset.Options(); opt.flavor = 'woff2'; opt.name_IDs = [1, 2]; opt.name_languages = [0x409]; opt.notdef_outline = True; opt.layout_features = []
sub = subset.Subsetter(opt); sub.populate(text='0123456789+-−!.,%×k ')
sub.subset(f)
for rec in list(f['name'].names): rec.string = 'RetroNum' if rec.nameID == 1 else 'Bold'
out = f'{ROOT}/game/assets/fonts/retronum.woff2'
subset.save_font(f, out, opt)
print(out, os.path.getsize(out), 'bytes')
