"""0.84 content: Portée also lengthens the blows of the area weapons (melee and slam weapons: their reach, not their
width), +2.5 % a level, +0.5 % a shop level, after Intelligence (game.js recompute: st.wreach; spells.js castMelee / slam).
usage: PYTHONUTF8=1 python tools/content/patch_084.py  (imports patch_081, writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_081 as P1

C, G, T, put_ui = P1.C, P1.G, P1.T, P1.put_ui

po = next(p for p in C['passives'] if p['id'] == 'portee')
po['reachW'], po['reachShop'] = 0.025, 0.005
ADD = T(" Allonge aussi de 2,5 % par niveau la portée des armes de zone (+0,5 % par niveau en boutique).",
        " Also lengthens the reach of area weapons by 2.5% per level (+0.5% per shop level).",
        " Verlängert außerdem die Reichweite der Flächenwaffen um 2,5 % pro Stufe (+0,5 % pro Shop-Stufe).",
        " También alarga un 2,5 % por nivel el alcance de las armas de área (+0,5 % por nivel en la tienda).",
        " Allunga anche del 2,5% per livello la portata delle armi ad area (+0,5% per livello nel negozio).",
        " Verlengt ook het bereik van gebiedswapens met 2,5% per niveau (+0,5% per winkelniveau).",
        " Também aumenta em 2,5% por nível o alcance das armas de área (+0,5% por nível na loja).")
for lg, s in ADD.items():
    if s.strip() not in po['desc'][lg]: po['desc'][lg] = po['desc'][lg].rstrip() + s

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.84 ok')
