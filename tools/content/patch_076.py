"""0.76 content: the Cawotte's zone is round now (gspells.js), its description says so.
usage: PYTHONUTF8=1 python tools/content/patch_076.py  (imports patch_068, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_068 as P8

C, G, T, put_ui = P8.C, P8.G, P8.T, P8.put_ui
S = C['spells']

S['cawotte']['desc'] = T("Une Cawotte jaillit sous vos pieds au milieu d'une zone ronde : restez dedans pour vous soigner. Le Wa Wabbit en pleure encore.",
                         "A Cawwot springs up under your feet in the middle of a round zone: stay inside to heal. The Wa Wabbit still cries about it.",
                         "Eine Kawotte springt unter deinen Füßen in einem runden Feld hervor: bleib darin, um dich zu heilen. Der Wa Wabbit weint noch.",
                         "Una Zanahowia brota bajo tus pies en medio de una zona redonda: quédate dentro para curarte. El Wa Wabbit aún llora.",
                         "Una Cawota spunta sotto i tuoi piedi al centro di una zona rotonda: restaci dentro per curarti. Il Wa Wabbit piange ancora.",
                         "Een Wortew schiet onder je voeten op midden in een rond gebied: blijf erin staan om te genezen. De Wa Wabbit huilt er nog om.",
                         "Uma Cenouwa brota debaixo dos teus pés no meio de uma zona redonda: fica dentro dela para te curares. O Wa Wabbit ainda chora.")

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.76 ok')
