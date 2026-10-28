"""Beta 0.28 content (lot 5F), applied on top of patch_027: the Armurerie (weapons, characteristics, TTG binder, treasure
maps, souls) and the synergies under the level-up choices (game/js/ui_armory.js).  ->  game/data/content.json
usage: python tools/content/patch_028.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_027 as P7

C, T, G = P7.C, P7.T, P7.G

UI = {
    'armory': T('Armurerie', 'Armoury', 'Waffenkammer', 'Armería', 'Armeria', 'Wapenkamer', 'Armaria'),
    'arm_weapons': T('Armes', 'Weapons', 'Waffen', 'Armas', 'Armi', 'Wapens', 'Armas'),
    'arm_stats': T('Caractéristiques', 'Characteristics', 'Eigenschaften', 'Características', 'Caratteristiche', 'Eigenschappen', 'Características'),
    'arm_tmaps': T('Cartes au trésor', 'Treasure maps', 'Schatzkarten', 'Mapas del tesoro', 'Mappe del tesoro', 'Schatkaarten', 'Mapas do tesouro'),
    'arm_boosted': T('Profite de', 'Boosted by', 'Profitiert von', 'Se beneficia de', 'Potenziato da', 'Profiteert van', 'Beneficia de'),
    'arm_finales': T('Évolutions finales (une seule par partie)', 'Final evolutions (only one per run)', 'Endentwicklungen (nur eine pro Lauf)', 'Evoluciones finales (solo una por partida)', 'Evoluzioni finali (una sola per partita)', 'Eindevoluties (maar één per run)', 'Evoluções finais (só uma por partida)'),
    'arm_found': T('Trouvée', 'Found', 'Gefunden', 'Encontrada', 'Trovata', 'Gevonden', 'Encontrada'),
    'arm_notyet': T('Pas encore… elle se cache bien.', 'Not yet… it hides well.', 'Noch nicht… sie versteckt sich gut.', 'Todavía no… se esconde bien.', 'Non ancora… si nasconde bene.', 'Nog niet… hij verstopt zich goed.', 'Ainda não… esconde-se bem.'),
    'arm_max': T('Niveau max : {n}', 'Max level: {n}', 'Max. Stufe: {n}', 'Nivel máx.: {n}', 'Livello max: {n}', 'Max. niveau: {n}', 'Nível máx.: {n}'),
    'arm_nospell': T('Aucun sort ne s\'en sert directement : c\'est pour vous, pas pour vos sorts.', 'No spell uses it directly: it\'s for you, not your spells.', 'Kein Zauber nutzt es direkt: Es ist für dich, nicht für deine Zauber.', 'Ningún hechizo lo usa directamente: es para ti, no para tus hechizos.', 'Nessun incantesimo lo usa direttamente: è per te, non per i tuoi incantesimi.', 'Geen spreuk gebruikt het direct: het is voor jou, niet voor je spreuken.', 'Nenhum feitiço o usa diretamente: é para ti, não para os teus feitiços.'),
    'ttg_empty': T('Le Classeur est prêt, mais la liste officielle des cartes TTG n\'a pas encore été importée. Les boosters arriveront avec elle.', 'The binder is ready, but the official TTG card list hasn\'t been imported yet. Boosters will come with it.', 'Der Ordner ist bereit, aber die offizielle TTG-Kartenliste wurde noch nicht importiert. Die Booster kommen mit ihr.', 'El archivador está listo, pero aún no se ha importado la lista oficial de cartas TTG. Los sobres llegarán con ella.', 'Il raccoglitore è pronto, ma la lista ufficiale delle carte TTG non è ancora stata importata. Le buste arriveranno con essa.', 'De map is klaar, maar de officiële TTG-kaartenlijst is nog niet geïmporteerd. De boosters komen daarmee.', 'O dossier está pronto, mas a lista oficial das cartas TTG ainda não foi importada. As saquetas chegarão com ela.'),
    'tmap_none': T('Aucune carte au trésor pour l\'instant. Musha l\'Oni en perd parfois dans les zones à secret… sans le faire exprès, évidemment.', 'No treasure map yet. Musha the Oni sometimes drops some in the zones with a secret… by accident, obviously.', 'Noch keine Schatzkarte. Oni Musha verliert manchmal welche in Zonen mit Geheimnis… natürlich aus Versehen.', 'Ningún mapa del tesoro por ahora. Musha el Oni a veces pierde alguno en las zonas con secreto… sin querer, claro.', 'Nessuna mappa del tesoro per ora. Musha l\'Oni a volte ne perde qualcuna nelle zone con un segreto… per sbaglio, ovviamente.', 'Nog geen schatkaart. Musha de Oni verliest er soms een in zones met een geheim… per ongeluk, natuurlijk.', 'Nenhum mapa do tesouro por agora. O Musha o Oni às vezes perde algum nas zonas com segredo… sem querer, claro.'),
    'tmap_todo': T('À creuser !', 'To dig up!', 'Ausgraben!', '¡Por desenterrar!', 'Da scavare!', 'Nog opgraven!', 'Por desenterrar!'),
    'tmap_done': T('Déterré', 'Dug up', 'Ausgegraben', 'Desenterrado', 'Dissotterrato', 'Opgegraven', 'Desenterrado'),
    'mastery': T('Maîtrise', 'Mastery', 'Beherrschung', 'Dominio', 'Maestria', 'Beheersing', 'Domínio'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg].setdefault(k, txt)

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.28 ok')
