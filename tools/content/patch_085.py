"""0.85 content: the relics' bonus summary strings (UI.relicSummary: 'relic_bonuses' + 'rb_<stat>' for
the stats no characteristic names), the picture-quality hint by resolution (720p / 1080p / QHD 1440p / 4K 2160p).
usage: PYTHONUTF8=1 python tools/content/patch_085.py  (imports patch_084, writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_084 as P4

C, G, T, put_ui = P4.C, P4.G, P4.T, P4.put_ui

put_ui({
    'relic_bonuses': T('Bonus des reliques', 'Relic bonuses', 'Relikt-Boni', 'Bonificaciones de reliquias', 'Bonus delle reliquie', 'Relikwiebonussen', 'Bónus das relíquias'),
    'rb_burn': T('Brûlure', 'Burn', 'Verbrennung', 'Quemadura', 'Ustione', 'Brandwond', 'Queimadura'),
    'rb_thorns': T('Épines', 'Thorns', 'Dornen', 'Espinas', 'Spine', 'Doornen', 'Espinhos'),
    'rb_critMult': T('Dégâts critiques', 'Critical damage', 'Kritischer Schaden', 'Daño crítico', 'Danni critici', 'Kritieke schade', 'Dano crítico'),
    'rb_healBonus': T('Soins reçus', 'Healing received', 'Erhaltene Heilung', 'Curación recibida', 'Cure ricevute', 'Ontvangen genezing', 'Cura recebida'),
    'rb_dashCd': T('Recharge de l\'esquive', 'Dash cooldown', 'Ausweich-Abklingzeit', 'Recarga del esquive', 'Ricarica della schivata', 'Ontwijk-hersteltijd', 'Recarga da esquiva'),
    'quality_hint': T("720p et 1080p allègent l'image, les sprites et les effets pour les PC peu puissants. QHD (1440p) : la qualité de référence. 4K (2160p) : pour les grands écrans.",
                      "720p and 1080p lighten the picture, sprites and effects for weaker PCs. QHD (1440p): the reference quality. 4K (2160p): for big screens.",
                      "720p und 1080p entlasten Bild, Sprites und Effekte für schwächere PCs. QHD (1440p): die Referenzqualität. 4K (2160p): für große Bildschirme.",
                      "720p y 1080p aligeran la imagen, los sprites y los efectos para PC poco potentes. QHD (1440p): la calidad de referencia. 4K (2160p): para pantallas grandes.",
                      "720p e 1080p alleggeriscono immagine, sprite ed effetti per i PC meno potenti. QHD (1440p): la qualità di riferimento. 4K (2160p): per i grandi schermi.",
                      "720p en 1080p verlichten beeld, sprites en effecten voor minder krachtige pc's. QHD (1440p): de referentiekwaliteit. 4K (2160p): voor grote schermen.",
                      "720p e 1080p aliviam a imagem, os sprites e os efeitos para PCs menos potentes. QHD (1440p): a qualidade de referência. 4K (2160p): para ecrãs grandes."),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.85 ok')
