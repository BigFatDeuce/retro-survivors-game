"""Beta 0.59 content, applied on top of patch_056.   usage: python tools/content/patch_059.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_056 as P6

C, G, T, put_ui = P6.C, P6.G, P6.T, P6.put_ui
# the crowd's hard cap was a number in game.js (420); spawnCap (600) stays what the waves aim for (and half of it the
# point under which they refill twice as fast): 420 kept, today's behaviour unchanged
C['run']['mobCap'] = 420
put_ui({
    # a permanent spell's duration (the Faux de Sacrieur's orbit: 1e9 s) on the level-up cards
    'permanent': T('permanente', 'permanent', 'unbegrenzt', 'permanente', 'permanente', 'permanent', 'permanente'),
    # the profile's save as a file (Options)
    'save_label': T('Sauvegarde du profil', 'Profile save', 'Spielstand des Profils', 'Guardado del perfil', 'Salvataggio del profilo', 'Opslag van het profiel', 'Salvamento do perfil'),
    'save_hint': T("Exporte la progression du profil dans un fichier (.json) pour la garder ou la passer sur un autre appareil. Importer remplace le profil actuel.",
                   "Exports the profile's progress to a file (.json) to keep it or move it to another device. Importing replaces the current profile.",
                   "Exportiert den Fortschritt des Profils in eine Datei (.json), um ihn aufzubewahren oder auf ein anderes Gerät zu bringen. Importieren ersetzt das aktuelle Profil.",
                   "Exporta el progreso del perfil a un archivo (.json) para guardarlo o pasarlo a otro dispositivo. Importar reemplaza el perfil actual.",
                   "Esporta i progressi del profilo in un file (.json) per conservarli o spostarli su un altro dispositivo. Importare sostituisce il profilo attuale.",
                   "Exporteert de voortgang van het profiel naar een bestand (.json) om te bewaren of naar een ander apparaat over te zetten. Importeren vervangt het huidige profiel.",
                   "Exporta o progresso do perfil para um arquivo (.json) para guardá-lo ou levá-lo para outro aparelho. Importar substitui o perfil atual."),
    'save_export': T('Exporter', 'Export', 'Exportieren', 'Exportar', 'Esporta', 'Exporteren', 'Exportar'),
    'save_import': T('Importer', 'Import', 'Importieren', 'Importar', 'Importa', 'Importeren', 'Importar'),
    'save_exported': T('Sauvegarde exportée', 'Save exported', 'Spielstand exportiert', 'Guardado exportado', 'Salvataggio esportato', 'Opslag geëxporteerd', 'Salvamento exportado'),
    'save_confirm': T('Remplacer {p} ?', 'Replace {p}?', '{p} ersetzen?', '¿Reemplazar {p}?', 'Sostituire {p}?', '{p} vervangen?', 'Substituir {p}?'),
    'save_bad': T("Ce fichier n'est pas une sauvegarde de Retro Survivors.", 'This file is not a Retro Survivors save.',
                  'Diese Datei ist kein Spielstand von Retro Survivors.', 'Este archivo no es un guardado de Retro Survivors.',
                  'Questo file non è un salvataggio di Retro Survivors.', 'Dit bestand is geen opslag van Retro Survivors.',
                  'Este arquivo não é um salvamento de Retro Survivors.'),
    'save_newer': T('Cette sauvegarde vient d’une version plus récente du jeu : mets le jeu à jour d’abord.',
                    'This save comes from a newer version of the game: update the game first.',
                    'Dieser Spielstand stammt aus einer neueren Version des Spiels: aktualisiere zuerst das Spiel.',
                    'Este guardado viene de una versión más reciente del juego: actualiza el juego primero.',
                    'Questo salvataggio viene da una versione più recente del gioco: aggiorna prima il gioco.',
                    'Deze opslag komt uit een nieuwere versie van het spel: werk het spel eerst bij.',
                    'Este salvamento vem de uma versão mais recente do jogo: atualize o jogo primeiro.'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.59 ok')
