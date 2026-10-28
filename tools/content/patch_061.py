"""0.61 content: the credits made shorter and proofread (no client version, no font line, no thanks line, no
counters; spelling / grammar; the Portuguese lines in the Brazilian Portuguese of the rest of the game), and the content
bugs found by the 0.61 global test: the 'Maître d'armes' achievement said level 10 (masteries stop at 5), the two bosses
that no zone ever shows (Kralamoure Géant, Maître Corbac) kept the bestiary at 99 %, 156 skins named '-' in Italian, the
'save_imported' toast had no text, 'Nettoyer les 12 zones' while 15 are visible, 'Epée' without its accent, hard-coded secret toasts.
usage: PYTHONUTF8=1 python tools/content/patch_061.py  (imports patch_060, writes game/data/content.json)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_060 as P0

C, G, T, put_ui = P0.C, P0.G, P0.T, P0.put_ui

# ---------------------------------------------------------------- credits
put_ui({
    'cr2': T('Tous les graphismes, sons, musiques, textes officiels et données de monstres proviennent du client Dofus Rétro : © Ankama Games.',
             'All graphics, sounds, music, official texts and monster data come from the Dofus Retro client: © Ankama Games.',
             'Alle Grafiken, Sounds, Musikstücke, offiziellen Texte und Monsterdaten stammen aus dem Dofus-Retro-Client: © Ankama Games.',
             'Todos los gráficos, sonidos, músicas, textos oficiales y datos de monstruos provienen del cliente de Dofus Retro: © Ankama Games.',
             'Tutta la grafica, i suoni, le musiche, i testi ufficiali e i dati dei mostri provengono dal client di Dofus Retro: © Ankama Games.',
             'Alle graphics, geluiden, muziek, officiële teksten en monstergegevens komen uit de Dofus Retro-client: © Ankama Games.',
             'Todos os gráficos, sons, músicas, textos oficiais e dados de monstros vêm do cliente Dofus Retro: © Ankama Games.'),
    'cr7': T("Ce jeu a été vibecodé, mais vibecodé avec la passion d'un nostalgique de Dofus qui a encore son Gelano de 2006 rangé quelque part. (Sûrement dans une poubelle.)",
             'This game was vibecoded, but vibecoded with the passion of a nostalgic Dofus player who still keeps his 2006 Gelano somewhere. (Probably in a bin.)',
             'Dieses Spiel wurde vibegecodet, aber mit der Leidenschaft eines Dofus-Nostalgikers, der seinen Gelano von 2006 noch irgendwo aufbewahrt. (Wahrscheinlich in einer Mülltonne.)',
             'Este juego fue vibecodeado, pero vibecodeado con la pasión de un nostálgico de Dofus que aún guarda su Gelano de 2006 en algún sitio. (Seguramente en una papelera.)',
             'Questo gioco è stato vibecodato, ma vibecodato con la passione di un nostalgico di Dofus che conserva ancora il suo Gelano del 2006 da qualche parte. (Probabilmente in un bidone.)',
             'Deze game is gevibecodet, maar met de passie van een Dofus-nostalgicus die zijn Gelano uit 2006 nog ergens bewaart. (Waarschijnlijk in een vuilnisbak.)',
             'Este jogo foi vibecodado, mas vibecodado com a paixão de um nostálgico de Dofus que ainda guarda seu Gelano de 2006 em algum lugar. (Provavelmente numa lixeira.)'),
    'cr8': T("Il ne sera jamais payant : l'argent n'a jamais été et ne sera jamais le moteur des jeux que je vibecode. Gardez vos kamas, vous en aurez besoin pour le Zaap.",
             "It will never cost a thing: money never was and never will be what drives the games I vibecode. Keep your kamas, you'll need them for the Zaap.",
             'Es wird nie etwas kosten: Geld war nie und wird nie der Antrieb der Spiele sein, die ich vibecode. Behaltet eure Kamas, ihr braucht sie für den Zaap.',
             'Nunca será de pago: el dinero nunca ha sido ni será el motor de los juegos que vibecodeo. Guardad vuestros kamas, los necesitaréis para el Zaap.',
             'Non sarà mai a pagamento: il denaro non è mai stato né mai sarà il motore dei giochi che vibecodo. Tenetevi i kama, vi serviranno per lo Zaap.',
             "Het zal nooit geld kosten: geld is nooit de drijfveer geweest van de games die ik vibecode, en dat blijft zo. Houd je kama's, je hebt ze nodig voor de Zaap.",
             'Nunca será pago: o dinheiro nunca foi nem será o motor dos jogos que eu vibecodo. Guardem seus kamas, vocês vão precisar deles para o Zaap.'),
    'cr9': T("Ankama mérite de perdurer, pas d'être exploitée. Mais il serait temps de se sortir les doigts du Slip de Trool et de bloquer enfin les bots : il n'y a jamais eu d'excuse, et avec l'IA d'aujourd'hui, il y en a encore moins pour ne pas détecter et bannir ces fermes à pognon que des petits malins nourrissent en leur achetant des kamas.",
             "Ankama deserves to last, not to be exploited. But it's time to take their fingers out of the Trool's Pants and finally block the bots: there never was an excuse, and with today's AI there's even less of one for not detecting and banning those money farms that clever clogs keep feeding by buying kamas.",
             'Ankama verdient es, zu bestehen, nicht ausgebeutet zu werden. Aber es wird Zeit, die Finger aus der Trool-Unterhose zu nehmen und endlich die Bots zu sperren: Es gab nie eine Ausrede, und mit der heutigen KI erst recht keine, diese Geldfarmen nicht zu erkennen und zu bannen, die schlaue Köpfe mit Kamakäufen füttern.',
             'Ankama merece perdurar, no ser explotada. Pero ya es hora de que se saquen los dedos del Calzón de Trool y bloqueen por fin los bots: nunca hubo excusa, y con la IA de hoy aún menos para no detectar ni banear esas granjas de dinero que algunos listillos alimentan comprando kamas.',
             "Ankama merita di durare, non di essere sfruttata. Ma è ora di togliere le dita dalle Mutande di Trool e bloccare finalmente i bot: non c'è mai stata una scusa, e con l'IA di oggi ancora meno per non scovare e bannare quelle fattorie di soldi che certi furbetti nutrono comprando kama.",
             "Ankama verdient het om te blijven bestaan, niet om uitgebuit te worden. Maar het wordt tijd om de vingers uit de Troolonderbroek te halen en eindelijk de bots te blokkeren: er was nooit een excuus, en met de AI van vandaag nog minder om die geldfarms niet op te sporen en te bannen die slimmeriken voeden door kama's te kopen.",
             'A Ankama merece perdurar, não ser explorada. Mas já está na hora de tirar os dedos das Cuecas de Trool e finalmente bloquear os bots: nunca houve desculpa, e com a IA de hoje há menos ainda para não detectar e banir essas fazendas de dinheiro que alguns espertinhos alimentam comprando kamas.'),
    'cr10': T('Et nerfez les Crâs sur Rétro. Bisou.', 'And nerf the Cras on Retro. Kisses.', 'Und nerft die Cras auf Retro. Küsschen.', 'Y nerfead a los Zurcarák en Retro. Besos.',
              'E nerfate i Cra su Retro. Bacio.', "En nerf de Cra's op Retro. Kusje.", 'E deem um nerf nos Cras do Retro. Beijos.'),
    'cr3': T("Ce projet est non officiel, gratuit et n'est pas affilié à Ankama.", 'This project is unofficial, free, and not affiliated with Ankama.',
             'Dieses Projekt ist inoffiziell, kostenlos und nicht mit Ankama verbunden.', 'Este proyecto no es oficial, es gratuito y no está afiliado a Ankama.',
             'Questo progetto non è ufficiale, è gratuito e non è affiliato ad Ankama.', 'Dit project is onofficieel, gratis en niet verbonden aan Ankama.',
             'Este projeto não é oficial, é gratuito e não tem afiliação com a Ankama.'),
    # (0.61, global test: the toast after a profile import showed its raw key)
    'save_imported': T('Profil importé : le jeu redémarre…', 'Profile imported: the game restarts…', 'Profil importiert: das Spiel startet neu…', 'Perfil importado: el juego se reinicia…',
                       'Profilo importato: il gioco si riavvia…', 'Profiel geïmporteerd: het spel start opnieuw…', 'Perfil importado: o jogo reinicia…'),
})

# ---------------------------------------------------------------- the global test's content bugs
A = {a['id']: a for a in C['achievements']}
A['mastery_max']['desc'] = T("Monter une maîtrise d'arme au niveau maximum (5).", 'Raise a weapon mastery to its top level (5).', 'Eine Waffenmeisterschaft auf die Höchststufe (5) bringen.',
                             'Subir una maestría de arma al nivel máximo (5).', "Portare una maestria d'arma al livello massimo (5).", 'Een wapenmeesterschap naar het hoogste niveau (5) brengen.',
                             'Levar uma maestria de arma ao nível máximo (5).')
A['win_all']['desc'] = T('Nettoyer 12 zones différentes.', 'Clear 12 different zones.', '12 verschiedene Zonen säubern.', 'Limpiar 12 zonas distintas.', 'Ripulire 12 zone diverse.',
                         '12 verschillende zones vrijmaken.', 'Limpar 12 zonas diferentes.')
for b in ('kralamoure', 'maitre_corbac'):   # in no zone, no wave, no summon: out of the bestiary's count (progress.js / ui.js)
    assert b in C['bosses']; C['bosses'][b]['unused'] = 1
nd = 0
for cat in ('hats', 'capes', 'pets'):
    for it in C.get(cat, []):
        n = it.get('name') or {}
        for lg in ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt'):
            if n.get(lg) == '-': n[lg] = n.get('en') if n.get('en') not in (None, '-') else n.get('fr'); nd += 1
for sp in C['spells'].values():
    nm = sp.get('name') or {}
    if isinstance(nm, dict) and nm.get('fr', '').startswith('Epée'): nm['fr'] = 'É' + nm['fr'][1:]

put_ui({
    'secret_tot': T('ToT : « Vous me cherchiez ? Je vous attends à {t}, au centre de la carte… »', "ToT: \"Looking for me? I'll be waiting at {t}, in the middle of the map…\"",
                    'ToT: „Sucht ihr mich? Ich warte um {t} in der Mitte der Karte…“', 'ToT: «¿Me buscabas? Te espero a las {t}, en el centro del mapa…»',
                    'ToT: «Mi cercavi? Ti aspetto alle {t}, al centro della mappa…»', 'ToT: "Zoek je mij? Ik wacht op je om {t}, in het midden van de kaart…"',
                    'ToT: «Está me procurando? Te espero às {t}, no centro do mapa…»'),
    'tofumode_off': T('Mode Tofu désactivé.', 'Tofu mode off.', 'Tofu-Modus aus.', 'Modo Tofu desactivado.', 'Modalità Tofu disattivata.', 'Tofu-modus uit.', 'Modo Tofu desativado.'),
    'secret_ankama': T('Ankama Games — 2004 · Merci pour le Monde des Douze ❤', 'Ankama Games — 2004 · Thank you for the World of Twelve ❤', 'Ankama Games — 2004 · Danke für die Welt der Zwölf ❤',
                       'Ankama Games — 2004 · Gracias por el Mundo de los Doce ❤', 'Ankama Games — 2004 · Grazie per il Mondo dei Dodici ❤', 'Ankama Games — 2004 · Bedankt voor de Wereld van Twaalf ❤',
                       'Ankama Games — 2004 · Obrigado pelo Mundo dos Doze ❤'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.61 ok', nd, "names '-' replaced")
