"""Beta 0.44 content, applied on top of patch_038.   usage: python tools/content/patch_039.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_038 as P8

C, T, G, put_ui = P8.C, P8.T, P8.G, P8.put_ui

# XP: the ambers (monsters' XP) -10 % again, the bosses' -50 %
for m in C['monsters'].values(): m['xp'] = round(m['xp'] * 0.9, 4)
for b in C['bosses'].values(): b['xp'] = round(b['xp'] * 0.5, 2)

# the performance mode becomes three picture qualities: SD (720p), HD (1080p), UHD (1440p, the default)
put_ui({
    'quality': T('Qualité graphique', 'Graphics quality', 'Grafikqualität', 'Calidad gráfica', 'Qualità grafica', 'Grafische kwaliteit', 'Qualidade gráfica'),
    'quality_hint': T('SD (720p) et HD (1080p) allègent l\'image, les sprites et les effets pour les PC peu puissants. UHD (1440p) : la pleine qualité.',
                      'SD (720p) and HD (1080p) lighten the picture, sprites and effects for less powerful PCs. UHD (1440p): full quality.',
                      'SD (720p) und HD (1080p) entlasten Bild, Sprites und Effekte für schwächere PCs. UHD (1440p): volle Qualität.',
                      'SD (720p) y HD (1080p) aligeran la imagen, los sprites y los efectos para PC modestos. UHD (1440p): calidad completa.',
                      'SD (720p) e HD (1080p) alleggeriscono immagine, sprite ed effetti per i PC meno potenti. UHD (1440p): qualità piena.',
                      'SD (720p) en HD (1080p) maken beeld, sprites en effecten lichter voor minder krachtige pc\'s. UHD (1440p): volle kwaliteit.',
                      'SD (720p) e HD (1080p) aliviam a imagem, os sprites e os efeitos para PCs menos potentes. UHD (1440p): qualidade total.'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.44 ok', round(C['monsters']['tofu']['xp'], 4) if 'tofu' in C['monsters'] else '', len(C['bosses']))
