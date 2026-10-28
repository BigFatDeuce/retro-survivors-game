"""Beta 0.31 content (lot 5I), applied on top of patch_029: 25 new achievements (the systems of 0.23-0.30 and a few
nods to the original game), with the counters they read (game/js/progress.js `value`, Prog.add in the game code).
->  game/data/content.json      usage: python tools/content/patch_030.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_029 as P9

C, T, G = P9.C, P9.T, P9.G

A = [  # id, counter, goal, item picture, name, description
    ('relic_5', 'bestRelics', 5, 'it_24_119',
     T('Brocanteur d\'Astrub', 'Astrub Junk Dealer', 'Trödler von Astrub', 'Chamarilero de Astrub', 'Rigattiere di Astrub', 'Uitdrager van Astrub', 'Adeleiro de Astrub'),
     T('Porter 5 reliques dans une même partie. Le sac pèse, mais ça brille.', 'Carry 5 relics in a single run. The bag is heavy, but it shines.', '5 Relikte in einem Lauf tragen. Der Sack ist schwer, aber er glänzt.', 'Llevar 5 reliquias en una misma partida. La bolsa pesa, pero brilla.', 'Portare 5 reliquie in una sola partita. La sacca pesa, ma luccica.', '5 relikwieën dragen in één run. De zak is zwaar, maar hij glimt.', 'Levar 5 relíquias numa só partida. O saco pesa, mas brilha.')),
    ('archi_10', 'archis', 10, 'it_83_12',
     T('Chasseur d\'Archimonstres', 'Archmonster Hunter', 'Erzmonsterjäger', 'Cazador de Archimonstruos', 'Cacciatore di Arcimostri', 'Aartsmonsterjager', 'Caçador de Arquimonstros'),
     T('Vaincre 10 Archimonstres. Ils avaient pourtant un nom à rallonge.', 'Defeat 10 Archmonsters. Despite their very long names.', '10 Erzmonster besiegen. Trotz ihrer ellenlangen Namen.', 'Vencer a 10 Archimonstruos. Y eso que tenían nombres larguísimos.', 'Sconfiggere 10 Arcimostri. Nonostante i loro nomi lunghissimi.', '10 Aartsmonsters verslaan. Ondanks hun ellenlange namen.', 'Vencer 10 Arquimonstros. Apesar dos nomes compridíssimos.')),
    ('souls_25', 'souls', 25, 'it_83_10',
     T('Pierre d\'âme bien remplie', 'A Well-Filled Soul Stone', 'Gut gefüllter Seelenstein', 'Piedra de alma bien llena', 'Pietra dell\'anima ben piena', 'Goed gevulde zielensteen', 'Pedra de alma bem cheia'),
     T('Capturer 25 âmes d\'Archimonstres différentes. Le Classeur dit merci.', 'Capture 25 different Archmonster souls. The binder says thanks.', '25 verschiedene Erzmonster-Seelen fangen. Der Ordner sagt danke.', 'Capturar 25 almas de Archimonstruos distintas. El archivador lo agradece.', 'Catturare 25 anime di Arcimostri diversi. Il raccoglitore ringrazia.', '25 verschillende aartsmonsterzielen vangen. De map zegt dankjewel.', 'Capturar 25 almas de Arquimonstros diferentes. O dossier agradece.')),
    ('endless_15', 'bestEndless', 900, 'it_43_37',
     T('Vers l\'infini et Astrub', 'To Infinity and Astrub', 'Bis zur Unendlichkeit und nach Astrub', 'Hasta el infinito y Astrub', 'Verso l\'infinito e Astrub', 'Naar oneindig en Astrub', 'Até ao infinito e Astrub'),
     T('Tenir 15 minutes en mode Infini. Xélor lui-même regarde sa montre.', 'Last 15 minutes in Endless mode. Xelor himself checks his watch.', '15 Minuten im Endlos-Modus durchhalten. Selbst Xelor schaut auf die Uhr.', 'Aguantar 15 minutos en modo Infinito. Hasta Xelor mira el reloj.', 'Resistere 15 minuti in modalità Infinita. Persino Xelor guarda l\'orologio.', '15 minuten volhouden in Eindeloze modus. Zelfs Xelor kijkt op zijn horloge.', 'Aguentar 15 minutos no modo Infinito. Até o Xelor olha para o relógio.')),
    ('events_10', 'randEvents', 10, 'it_15_90',
     T('Touriste de l\'imprévu', 'Tourist of the Unexpected', 'Tourist des Unerwarteten', 'Turista de lo imprevisto', 'Turista dell\'imprevisto', 'Toerist van het onverwachte', 'Turista do imprevisto'),
     T('Vivre 10 événements aléatoires. Une invasion de Bworks, ça occupe un dimanche.', 'Live through 10 random events. A Bwork invasion keeps a Sunday busy.', '10 Zufallsereignisse erleben. Eine Bwork-Invasion füllt jeden Sonntag.', 'Vivir 10 eventos aleatorios. Una invasión de Bworks llena cualquier domingo.', 'Vivere 10 eventi casuali. Un\'invasione di Bwork riempie la domenica.', '10 willekeurige gebeurtenissen beleven. Een Bwork-invasie vult je zondag.', 'Viver 10 eventos aleatórios. Uma invasão de Bworks ocupa um domingo.')),
    ('unique_1', 'uniquesKinds', 1, 'it_2_31',
     T('Arme de légende', 'Legendary Weapon', 'Legendäre Waffe', 'Arma de leyenda', 'Arma leggendaria', 'Legendarisch wapen', 'Arma lendária'),
     T('Trouver une arme unique. Ne pas la revendre à l\'HDV, promis ?', 'Find a unique weapon. Don\'t sell it at the market, promise?', 'Eine einzigartige Waffe finden. Nicht im Auktionshaus verkaufen, versprochen?', 'Encontrar un arma única. No la vendas en el mercadillo, ¿prometido?', 'Trovare un\'arma unica. Non rivenderla al mercato, promesso?', 'Een uniek wapen vinden. Niet op de markt verkopen, beloofd?', 'Encontrar uma arma única. Não a vendas no mercado, prometido?')),
    ('unique_all', 'uniquesAll', 1, 'it_4_7',
     T('Armurier du Krosmoz', 'Krosmoz Armourer', 'Waffenschmied des Krosmoz', 'Armero del Krosmoz', 'Armaiolo del Krosmoz', 'Wapensmid van de Krosmoz', 'Armeiro do Krosmoz'),
     T('Trouver toutes les armes uniques. Il va falloir agrandir le coffre.', 'Find every unique weapon. You\'ll need a bigger chest.', 'Alle einzigartigen Waffen finden. Du brauchst eine größere Truhe.', 'Encontrar todas las armas únicas. Hará falta un cofre más grande.', 'Trovare tutte le armi uniche. Servirà un baule più grande.', 'Alle unieke wapens vinden. Je hebt een grotere kist nodig.', 'Encontrar todas as armas únicas. Vai ser preciso um baú maior.')),
    ('fusion_1', 'fusions', 1, 'it_78_43',
     T('Forgemage du dimanche', 'Sunday Smithmagus', 'Sonntags-Schmiedemagier', 'Forjamago de domingo', 'Forgiamago della domenica', 'Zondagse smeedmagiër', 'Forjamago de domingo'),
     T('Fusionner une arme. Sans casser la rune, pour une fois.', 'Fuse a weapon. Without breaking the rune, for once.', 'Eine Waffe verschmelzen. Ausnahmsweise ohne die Rune zu zerbrechen.', 'Fusionar un arma. Sin romper la runa, por una vez.', 'Fondere un\'arma. Senza rompere la runa, per una volta.', 'Een wapen fuseren. Zonder de rune te breken, voor één keer.', 'Fundir uma arma. Sem partir a runa, por uma vez.')),
    ('wheel_10', 'wheels', 10, 'it_15_737',
     T('Accro à la Foire du Trool', 'Trool Fair Addict', 'Süchtig nach dem Trool-Jahrmarkt', 'Adicto a la Feria del Trool', 'Fanatico della Fiera del Trool', 'Verslaafd aan de Troolkermis', 'Viciado na Feira do Trool'),
     T('Faire tourner la roue du Trool 10 fois. La maison gagne toujours… presque.', 'Spin the Trool wheel 10 times. The house always wins… almost.', 'Das Trool-Rad 10-mal drehen. Die Bank gewinnt immer… fast.', 'Girar la rueda del Trool 10 veces. La banca siempre gana… casi.', 'Girare la ruota del Trool 10 volte. Il banco vince sempre… quasi.', 'Het Troolrad 10 keer draaien. De bank wint altijd… bijna.', 'Girar a roda do Trool 10 vezes. A casa ganha sempre… quase.')),
    ('jackpot', 'jackpots', 1, 'it_21_1',
     T('Bonne Pioche !', 'Lucky Strike!', 'Glückstreffer!', '¡Buena Piqueta!', 'Bel colpo di piccone!', 'Gouden houweel!', 'Boa Picareta!'),
     T('Toucher le gros lot de la bonne Pioche. Un Enutrof en pleure encore.', 'Hit the jackpot with La bonne Pioche. An Enutrof is still crying.', 'Mit der Guten Spitzhacke den Jackpot knacken. Ein Enutrof weint noch immer.', 'Ganar el premio gordo de la Buena Piqueta. Un Anutrof aún llora.', 'Vincere il jackpot della Buona Piccone. Un Enutrof piange ancora.', 'De jackpot winnen met het Goede Houweel. Een Enutrof huilt nog steeds.', 'Ganhar o prémio da Boa Picareta. Um Enutrof ainda chora.')),
    ('mutant', 'mutants', 1, 'it_105_38',
     T('Tofu pas frais', 'Not-So-Fresh Tofu', 'Nicht ganz frischer Tofu', 'Tofu poco fresco', 'Tofu non freschissimo', 'Niet-zo-verse Tofu', 'Tofu pouco fresco'),
     T('Rattraper et vaincre le Tofu Mutant. Il courait vite, pour un poulet.', 'Catch and defeat the Mutant Tofu. Fast, for a chicken.', 'Den Mutanten-Tofu einholen und besiegen. Schnell, für ein Huhn.', 'Alcanzar y vencer al Tofu Mutante. Rápido, para ser un pollo.', 'Raggiungere e sconfiggere il Tofu Mutante. Veloce, per un pollo.', 'De Mutantentofu inhalen en verslaan. Snel, voor een kip.', 'Apanhar e vencer o Tofu Mutante. Rápido, para uma galinha.')),
    ('portal', 'portals', 1, 'it_43_30',
     T('Retour vers le passé', 'Back to the Past', 'Zurück in die Vergangenheit', 'Regreso al pasado', 'Ritorno al passato', 'Terug naar het verleden', 'Regresso ao passado'),
     T('Franchir le portail temporel de ToT. Pensez à ne croiser personne.', 'Step through ToT\'s time portal. Try not to meet yourself.', 'Durch ToTs Zeitportal gehen. Begegne dir bloß nicht selbst.', 'Cruzar el portal temporal de ToT. Procura no cruzarte contigo.', 'Attraversare il portale temporale di ToT. Cerca di non incontrarti.', 'Door ToTs tijdportaal gaan. Kom jezelf niet tegen.', 'Atravessar o portal temporal do ToT. Tenta não te cruzares contigo.')),
    ('coffre', 'coffres', 1, 'it_15_13',
     T('Le coffre qui mord', 'The Chest That Bites', 'Die Truhe, die beißt', 'El cofre que muerde', 'Il forziere che morde', 'De kist die bijt', 'O baú que morde'),
     T('Vaincre le Coffre Animé. Ses dents valaient plus que son contenu.', 'Defeat the Animated Chest. Its teeth were worth more than its loot.', 'Die Lebende Truhe besiegen. Ihre Zähne waren mehr wert als ihr Inhalt.', 'Vencer al Cofre Animado. Sus dientes valían más que su contenido.', 'Sconfiggere il Forziere Animato. I denti valevano più del contenuto.', 'De Levende Kist verslaan. Zijn tanden waren meer waard dan de inhoud.', 'Vencer o Baú Animado. Os dentes valiam mais do que o conteúdo.')),
    ('tmap_1', 'tmapsDug', 1, 'it_24_7',
     T('La croix marque l\'endroit', 'X Marks the Spot', 'X markiert die Stelle', 'La X marca el lugar', 'La X segna il punto', 'X markeert de plek', 'O X marca o local'),
     T('Déterrer le trésor d\'une carte de Musha l\'Oni. Il jure que ce n\'était pas à lui.', 'Dig up the treasure of one of Musha the Oni\'s maps. He swears it wasn\'t his.', 'Den Schatz einer Karte von Oni Musha ausgraben. Er schwört, es war nicht seiner.', 'Desenterrar el tesoro de un mapa de Musha el Oni. Jura que no era suyo.', 'Dissotterrare il tesoro di una mappa di Musha l\'Oni. Giura che non era suo.', 'De schat van een kaart van Musha de Oni opgraven. Hij zweert dat hij niet van hem was.', 'Desenterrar o tesouro de um mapa do Musha o Oni. Jura que não era dele.')),
    ('hard_win', 'hardWins', 1, 'it_47_26',
     T('Même pas mal', 'Didn\'t Even Hurt', 'Tat nicht mal weh', 'Ni me ha dolido', 'Neanche un graffio', 'Deed niet eens pijn', 'Nem doeu'),
     T('Vaincre un boss final en mode Difficile. Le crâne de Crâ approuve.', 'Defeat a final boss in Hard mode. The Cra skull approves.', 'Einen Endboss im Schwer-Modus besiegen. Der Cra-Schädel nickt.', 'Vencer a un jefe final en modo Difícil. El cráneo de Zurcarák aprueba.', 'Sconfiggere un boss finale in Difficile. Il teschio di Cra approva.', 'Een eindbaas verslaan in Moeilijk. De Cra-schedel keurt het goed.', 'Vencer um chefe final no modo Difícil. O crânio de Cra aprova.')),
    ('hard_5', 'hardClasses', 5, 'it_47_27',
     T('Masochiste des Douze', 'Masochist of the Twelve', 'Masochist der Zwölf', 'Masoquista de los Doce', 'Masochista dei Dodici', 'Masochist van de Twaalf', 'Masoquista dos Doze'),
     T('Gagner en Difficile avec 5 classes différentes. Un Sacrieur trouve ça normal.', 'Win in Hard mode with 5 different classes. A Sacrier finds that normal.', 'Mit 5 verschiedenen Klassen im Schwer-Modus gewinnen. Ein Sacrieur findet das normal.', 'Ganar en Difícil con 5 clases distintas. Un Sacrogrito lo ve normal.', 'Vincere in Difficile con 5 classi diverse. Un Sacrier lo trova normale.', 'Winnen in Moeilijk met 5 verschillende klassen. Een Sacrier vindt dat normaal.', 'Ganhar no Difícil com 5 classes diferentes. Um Sacrier acha normal.')),
    ('ogivol', 'boss_ogivol', 1, 'it_32_9',
     T('Écailles et mauvaise humeur', 'Scales and Bad Temper', 'Schuppen und schlechte Laune', 'Escamas y mal humor', 'Scaglie e malumore', 'Schubben en slecht humeur', 'Escamas e mau humor'),
     T('Vaincre Ogivol Scalarcin dans les Landes de Sidimote. Il crachera ailleurs.', 'Defeat Ogivol Scalarcin in the Sidimote Moors. He\'ll spit elsewhere.', 'Ogivol Scalarcin in der Sidimote-Heide besiegen. Er spuckt jetzt woanders.', 'Vencer a Ogivol Escalarcín en las Landas de Sidimote. Escupirá en otro sitio.', 'Sconfiggere Ogivol Scalarcin nelle Lande di Sidimote. Sputerà altrove.', 'Ogivol Scalarcin verslaan in de Sidimote-heide. Hij spuwt voortaan elders.', 'Vencer Ogivol Scalarcin nas Charnecas de Sidimote. Vai cuspir para outro lado.')),
    ('ougah', 'boss_ougah', 1, 'it_15_40',
     T('Sorti de la tourbière', 'Out of the Bog', 'Raus aus dem Moor', 'Fuera de la turbera', 'Fuori dalla torbiera', 'Het veen uit', 'Fora da turfeira'),
     T('Vaincre Ougah sur la côte d\'Otomaï. Il ne vous attirera plus.', 'Defeat Ougah on the Otomai coast. He won\'t pull you in anymore.', 'Ougah an der Küste von Otomai besiegen. Er zieht dich nicht mehr an.', 'Vencer a Ougah en la costa de Otomai. Ya no te atraerá.', 'Sconfiggere Ougah sulla costa di Otomai. Non ti attirerà più.', 'Ougah verslaan aan de kust van Otomaï. Hij trekt je niet meer aan.', 'Vencer Ougah na costa de Otomai. Já não te vai atrair.')),
    ('crows_100', 'doomCrows', 100, 'it_15_329',
     T('Épouvantail', 'Scarecrow', 'Vogelscheuche', 'Espantapájaros', 'Spaventapasseri', 'Vogelverschrikker', 'Espantalho'),
     T('Abattre 100 Corbacs des Maîtres Corbacs. Ils reviendront, ils reviennent toujours.', 'Down 100 of the Masters\' Crobaks. They\'ll be back, they always are.', '100 Korbacks der Korback-Meister erledigen. Sie kommen wieder, wie immer.', 'Abatir 100 Corbacs de los Maestros Corbac. Volverán, siempre vuelven.', 'Abbattere 100 Corbac dei Maestri Corbac. Torneranno, tornano sempre.', '100 Kraaiers van de Meesterkraaiers neerhalen. Ze komen terug, altijd.', 'Abater 100 Corbacs dos Mestres Corbac. Voltarão, voltam sempre.')),
    ('tofu_death', 'tofuDeaths', 1, 'it_47_37',
     T('Humilié par un Tofu', 'Humbled by a Tofu', 'Von einem Tofu gedemütigt', 'Humillado por un Tofu', 'Umiliato da un Tofu', 'Vernederd door een Tofu', 'Humilhado por um Tofu'),
     T('Être vaincu par un Tofu. On dira que c\'était un Tofu Royal.', 'Be defeated by a Tofu. We\'ll say it was a Royal Tofu.', 'Von einem Tofu besiegt werden. Wir sagen, es war ein Königlicher Tofu.', 'Ser derrotado por un Tofu. Diremos que era un Tofu Real.', 'Essere sconfitto da un Tofu. Diremo che era un Tofu Reale.', 'Verslagen worden door een Tofu. We zeggen wel dat het een Koninklijke Tofu was.', 'Ser derrotado por um Tofu. Diremos que era um Tofu Real.')),
    ('quick_death', 'quickDeaths', 1, 'it_12_17',
     T('Potion de Rappel express', 'Express Recall Potion', 'Express-Rückrufpotion', 'Poción de Regreso exprés', 'Pozione di Richiamo express', 'Express-terugroepdrank', 'Poção de Regresso expresso'),
     T('Mourir avant la première minute. Le Zaap n\'a même pas eu le temps de refroidir.', 'Die before the first minute. The Zaap hadn\'t even cooled down.', 'Vor der ersten Minute sterben. Der Zaap war noch nicht mal abgekühlt.', 'Morir antes del primer minuto. El Zaap ni se había enfriado.', 'Morire prima del primo minuto. Lo Zaap non si era nemmeno raffreddato.', 'Doodgaan vóór de eerste minuut. De Zaap was nog niet eens afgekoeld.', 'Morrer antes do primeiro minuto. O Zaap nem tinha arrefecido.')),
    ('spent_100k', 'kamasSpent', 100000, 'it_15_268',
     T('Client fidèle', 'Loyal Customer', 'Treuer Kunde', 'Cliente fiel', 'Cliente fedele', 'Trouwe klant', 'Cliente fiel'),
     T('Dépenser 100 000 kamas en boutique. Le marchand a acheté un Dragodinde.', 'Spend 100,000 kamas in the shop. The merchant bought a Dragoturkey.', '100.000 Kamas im Laden ausgeben. Der Händler hat sich einen Drachentruthahn gekauft.', 'Gastar 100 000 kamas en la tienda. El mercader se compró un Dragopavo.', 'Spendere 100.000 kama nel negozio. Il mercante si è comprato un Dragacchino.', '100.000 kama uitgeven in de winkel. De handelaar kocht een Draakkalkoen.', 'Gastar 100 000 kamas na loja. O mercador comprou um Dragoperu.')),
    ('zones_played', 'zonesPlayed', 12, 'it_24_61',
     T('Tour du Monde des Douze', 'Tour of the World of Twelve', 'Reise durch die Welt der Zwölf', 'Vuelta al Mundo de los Doce', 'Giro del Mondo dei Dodici', 'Rondje Wereld van de Twaalf', 'Volta ao Mundo dos Doze'),
     T('Jouer dans 12 zones différentes. Sans Zaaps ni Dragodinde, en plus.', 'Play in 12 different zones. Without Zaaps or Dragoturkey, too.', 'In 12 verschiedenen Zonen spielen. Ohne Zaaps und ohne Drachentruthahn.', 'Jugar en 12 zonas distintas. Sin Zaaps ni Dragopavo, encima.', 'Giocare in 12 zone diverse. Senza Zaap né Dragacchino, per giunta.', 'In 12 verschillende zones spelen. Zonder Zaaps of Draakkalkoen nog wel.', 'Jogar em 12 zonas diferentes. Sem Zaaps nem Dragoperu, ainda por cima.')),
    ('rerolls_50', 'rerolls', 50, 'it_9_32',
     T('Ecaflip dans l\'âme', 'Ecaflip at Heart', 'Ecaflip im Herzen', 'Zurcarák de corazón', 'Ecaflip nell\'anima', 'Ecaflip in hart en nieren', 'Ecaflip de alma'),
     T('Relancer les choix 50 fois. Le chat-dieu adore votre style.', 'Reroll the choices 50 times. The cat god loves your style.', 'Die Auswahl 50-mal neu würfeln. Der Katzengott liebt deinen Stil.', 'Volver a tirar las opciones 50 veces. Al dios gato le encanta tu estilo.', 'Rilanciare le scelte 50 volte. Il dio gatto adora il tuo stile.', 'De keuzes 50 keer opnieuw gooien. De kattengod is dol op je stijl.', 'Relançar as escolhas 50 vezes. O deus-gato adora o teu estilo.')),
    ('kamas_1m', 'kamasEarned', 1000000, 'it_40_241',
     T('Le rêve d\'un Enutrof', 'An Enutrof\'s Dream', 'Der Traum eines Enutrof', 'El sueño de un Anutrof', 'Il sogno di un Enutrof', 'De droom van een Enutrof', 'O sonho de um Enutrof'),
     T('Gagner 1 000 000 de kamas au total. Il faudra un plus gros matelas.', 'Earn 1,000,000 kamas in total. You\'ll need a bigger mattress.', 'Insgesamt 1.000.000 Kamas verdienen. Du brauchst eine dickere Matratze.', 'Ganar 1 000 000 de kamas en total. Hará falta un colchón más grande.', 'Guadagnare 1.000.000 di kama in totale. Servirà un materasso più grande.', 'In totaal 1.000.000 kama verdienen. Je hebt een dikkere matras nodig.', 'Ganhar 1 000 000 de kamas no total. Vai ser preciso um colchão maior.')),
]
for a in C['achievements']:   # (two achievements shared the Plume du Maître Corbac)
    if a['id'] == 'doom': a['icon'] = 'it_24_40'
have = {a['id'] for a in C['achievements']}
for i, k, n, icon, name, desc in A:
    if i not in have: C['achievements'].append(dict(id=i, k=k, n=n, icon=icon, name=name, desc=desc))

# ---------------------------------------------------------------- humour pass (the texts that were only technical): a
# short joke after the characteristics, the class bonuses and the shop intros, and 10 more loading tips
JOKE = {
    'vitalite': T('Plus de PV, plus de temps pour fuir.', 'More HP, more time to run.', 'Mehr LP, mehr Zeit zum Wegrennen.', 'Más PV, más tiempo para huir.', 'Più PV, più tempo per scappare.', 'Meer HP, meer tijd om te vluchten.', 'Mais PV, mais tempo para fugir.'),
    'sagesse': T('Les livres servent enfin à quelque chose.', 'Books are finally good for something.', 'Bücher sind endlich zu etwas gut.', 'Los libros por fin sirven de algo.', 'I libri servono finalmente a qualcosa.', 'Boeken zijn eindelijk ergens goed voor.', 'Os livros finalmente servem para algo.'),
    'force': T('Frapper d\'abord, réfléchir jamais.', 'Hit first, think never.', 'Erst zuschlagen, nie nachdenken.', 'Primero pegar, pensar nunca.', 'Prima colpire, pensare mai.', 'Eerst slaan, nooit nadenken.', 'Primeiro bater, pensar nunca.'),
    'intelligence': T('Les Tofus ne savent plus où se cacher.', 'The Tofus have nowhere left to hide.', 'Die Tofus wissen nicht mehr, wohin.', 'Los Tofus ya no saben dónde esconderse.', 'I Tofu non sanno più dove nascondersi.', 'De Tofu\'s kunnen zich nergens meer verstoppen.', 'Os Tofus já não sabem onde se esconder.'),
    'chance': T('Ecaflip vous fait un clin d\'œil.', 'Ecaflip winks at you.', 'Ecaflip zwinkert dir zu.', 'Zurcarák te guiña un ojo.', 'Ecaflip ti fa l\'occhiolino.', 'Ecaflip knipoogt naar je.', 'O Ecaflip pisca-te o olho.'),
    'agilite': T('Pile dans le mille. Ou presque.', 'Right on target. Almost.', 'Volltreffer. Fast.', 'En el blanco. O casi.', 'Centro perfetto. Quasi.', 'Raak. Bijna.', 'Mesmo no alvo. Ou quase.'),
    'pa': T('Un PA de plus, comme au bon vieux temps.', 'One more AP, like the good old days.', 'Ein AP mehr, wie in alten Zeiten.', 'Un PA más, como en los viejos tiempos.', 'Un PA in più, come ai bei tempi.', 'Eén AP extra, net als vroeger.', 'Mais um PA, como nos velhos tempos.'),
    'pm': T('Les Tofus n\'ont qu\'à bien se tenir.', 'The Tofus had better watch out.', 'Die Tofus sollten sich warm anziehen.', 'Que se anden con ojo los Tofus.', 'I Tofu stiano in guardia.', 'De Tofu\'s kunnen maar beter oppassen.', 'Os Tofus que se cuidem.'),
    'portee': T('Le Crâ du coin est jaloux.', 'The local Cra is jealous.', 'Der Cra von nebenan ist neidisch.', 'El Ocra del barrio tiene envidia.', 'Il Cra del quartiere è geloso.', 'De Cra uit de buurt is jaloers.', 'O Cra do bairro está com inveja.'),
    'invocations': T('Plus on est de fous, plus on tape.', 'The more the merrier, the harder they hit.', 'Je mehr, desto härter.', 'Cuantos más, más golpes.', 'Più siamo, più picchiamo.', 'Hoe meer zielen, hoe harder de klappen.', 'Quantos mais, mais pancada.'),
    'soins': T('Un pansement n\'a jamais fait de mal.', 'A bandage never hurt anyone.', 'Ein Pflaster hat noch nie geschadet.', 'Una tirita nunca hizo daño.', 'Un cerotto non ha mai fatto male.', 'Een pleister heeft nooit kwaad gedaan.', 'Um penso nunca fez mal a ninguém.'),
    'prospection': T('L\'Enutrof en vous se réveille.', 'The Enutrof in you wakes up.', 'Der Enutrof in dir erwacht.', 'El Anutrof que llevas dentro despierta.', 'L\'Enutrof che è in te si sveglia.', 'De Enutrof in jou wordt wakker.', 'O Enutrof dentro de ti acorda.'),
    'resistances': T('Ça pique moins. Un peu.', 'It stings less. A bit.', 'Es tut weniger weh. Ein bisschen.', 'Pica menos. Un poco.', 'Fa meno male. Un po\'.', 'Het prikt minder. Een beetje.', 'Pica menos. Um pouco.'),
    'duree': T('Xélor a prolongé le bail.', 'Xelor extended the lease.', 'Xelor hat den Mietvertrag verlängert.', 'Xelor ha prorrogado el contrato.', 'Xelor ha rinnovato il contratto.', 'Xelor heeft het huurcontract verlengd.', 'O Xelor renovou o contrato.'),
    'vol_de_vie': T('Comme un Sacrieur, en plus poli.', 'Like a Sacrier, only politer.', 'Wie ein Sacrieur, nur höflicher.', 'Como un Sacrogrito, pero más educado.', 'Come un Sacrier, ma più educato.', 'Zoals een Sacrier, maar beleefder.', 'Como um Sacrier, mas mais educado.'),
    'renvoi': T('Qui s\'y frotte s\'y pique.', 'Touch me and regret it.', 'Wer sich anlegt, bereut es.', 'Quien se acerca, se pincha.', 'Chi tocca, si punge.', 'Wie aanraakt, krijgt prik.', 'Quem se mete, pica-se.'),
    'esquive': T('Glissant comme une anguille d\'Otomaï.', 'Slippery as an Otomai eel.', 'Glitschig wie ein Aal aus Otomai.', 'Escurridizo como una anguila de Otomai.', 'Sfuggente come un\'anguilla di Otomai.', 'Glad als een paling uit Otomaï.', 'Escorregadio como uma enguia de Otomai.'),
    'phenix': T('Le Zaap de la dernière chance.', 'The last-chance Zaap.', 'Der Zaap der letzten Chance.', 'El Zaap de la última oportunidad.', 'Lo Zaap dell\'ultima occasione.', 'De Zaap van de laatste kans.', 'O Zaap da última oportunidade.'),
    'borne': T('Têtu comme un Iop.', 'Stubborn as an Iop.', 'Stur wie ein Iop.', 'Terco como un Iop.', 'Testardo come un Iop.', 'Koppig als een Iop.', 'Teimoso como um Iop.'),
}
for pa in C['passives']:
    j = JOKE.get(pa['id'])
    if j: pa['desc'] = {lg: pa['desc'][lg] + ' ' + j[lg] for lg in pa['desc']}
CJOKE = {
    'feca': T('Le bouclier, c\'est la vie.', 'Shields are life.', 'Schilde sind das Leben.', 'El escudo es la vida.', 'Lo scudo è vita.', 'Een schild is het leven.', 'O escudo é a vida.'),
    'osamodas': T('Toujours une bestiole sous la main.', 'Always a critter at hand.', 'Immer ein Viech zur Hand.', 'Siempre un bicho a mano.', 'Sempre una bestiola a portata di mano.', 'Altijd een beestje bij de hand.', 'Sempre um bicho à mão.'),
    'enutrof': T('Une pièce par terre ? Elle est à lui.', 'A coin on the floor? It\'s his.', 'Eine Münze am Boden? Gehört ihm.', '¿Una moneda en el suelo? Es suya.', 'Una moneta per terra? È sua.', 'Een munt op de grond? Van hem.', 'Uma moeda no chão? É dele.'),
    'sram': T('On ne le voit pas venir. Littéralement.', 'You don\'t see him coming. Literally.', 'Man sieht ihn nicht kommen. Wörtlich.', 'No lo ves venir. Literalmente.', 'Non lo vedi arrivare. Letteralmente.', 'Je ziet hem niet aankomen. Letterlijk.', 'Não o vês chegar. Literalmente.'),
    'xelor': T('Jamais en retard, toujours en avance.', 'Never late, always early.', 'Nie zu spät, immer zu früh.', 'Nunca tarde, siempre pronto.', 'Mai in ritardo, sempre in anticipo.', 'Nooit te laat, altijd te vroeg.', 'Nunca atrasado, sempre adiantado.'),
    'ecaflip': T('Pile je gagne, face tu perds.', 'Heads I win, tails you lose.', 'Kopf gewinne ich, Zahl verlierst du.', 'Cara gano yo, cruz pierdes tú.', 'Testa vinco io, croce perdi tu.', 'Kop win ik, munt verlies jij.', 'Cara ganho eu, coroa perdes tu.'),
    'eniripsa': T('Un mot gentil et ça repart.', 'One kind word and off you go.', 'Ein nettes Wort und weiter geht\'s.', 'Una palabra amable y a seguir.', 'Una parola gentile e si riparte.', 'Eén lief woord en je kunt weer.', 'Uma palavra simpática e lá vai.'),
    'iop': T('Réfléchir ? Pour quoi faire ?', 'Think? What for?', 'Nachdenken? Wozu?', '¿Pensar? ¿Para qué?', 'Pensare? A che pro?', 'Nadenken? Waarom?', 'Pensar? Para quê?'),
    'cra': T('La distance de sécurité, c\'est sacré.', 'Safety distance is sacred.', 'Sicherheitsabstand ist heilig.', 'La distancia de seguridad es sagrada.', 'La distanza di sicurezza è sacra.', 'Veiligheidsafstand is heilig.', 'A distância de segurança é sagrada.'),
    'sadida': T('La nature ne pardonne pas.', 'Nature does not forgive.', 'Die Natur verzeiht nicht.', 'La naturaleza no perdona.', 'La natura non perdona.', 'De natuur vergeeft niet.', 'A natureza não perdoa.'),
    'sacrieur': T('Plus il saigne, plus il cogne.', 'The more he bleeds, the harder he hits.', 'Je mehr er blutet, desto härter haut er zu.', 'Cuanto más sangra, más pega.', 'Più sanguina, più picchia.', 'Hoe meer hij bloedt, hoe harder hij slaat.', 'Quanto mais sangra, mais bate.'),
    'pandawa': T('Un lait de bambou et tout tourne.', 'One bamboo milk and everything spins.', 'Eine Bambusmilch und alles dreht sich.', 'Una leche de bambú y todo da vueltas.', 'Un latte di bambù e tutto gira.', 'Eén bamboemelk en alles draait.', 'Um leite de bambu e tudo gira.'),
    'roublard': T('Boum. Rebelote. Boum.', 'Boom. Again. Boom.', 'Bumm. Nochmal. Bumm.', 'Bum. Otra vez. Bum.', 'Bum. Di nuovo. Bum.', 'Boem. Nog eens. Boem.', 'Bum. Outra vez. Bum.'),
    'bandit': T('Ce qui est à vous est à lui.', 'What\'s yours is his.', 'Was deins ist, ist seins.', 'Lo tuyo es suyo.', 'Ciò che è tuo è suo.', 'Wat van jou is, is van hem.', 'O que é teu é dele.'),
}
for c in C['classes']:
    j = CJOKE.get(c['id'])
    if j: c['passive'] = {lg: c['passive'][lg] + ' ' + j[lg] for lg in c['passive']}
UJOKE = {
    'pet_bonus': T('Même chez ToT. Il ne paie jamais sa part.', 'Even at ToT\'s. He never pays his share.', 'Sogar bei ToT. Er zahlt nie seinen Anteil.', 'Incluso donde ToT. Nunca paga su parte.', 'Persino da ToT. Non paga mai la sua parte.', 'Zelfs bij ToT. Hij betaalt nooit mee.', 'Até em casa do ToT. Nunca paga a sua parte.'),
    'scroll_intro': T('Le parchotage, sans les larmes.', 'Scrolling stats, without the tears.', 'Pergamente lesen, ohne Tränen.', 'Pergaminear, sin lágrimas.', 'Pergamenare, senza lacrime.', 'Perkamenten lezen, zonder tranen.', 'Pergaminhar, sem lágrimas.'),
    'mastery_intro': T('Le mannequin d\'entraînement n\'a rien demandé.', 'The training dummy didn\'t ask for this.', 'Die Trainingspuppe hat nicht darum gebeten.', 'El muñeco de entrenamiento no pidió nada.', 'Il manichino non ha chiesto niente.', 'De oefenpop heeft hier niet om gevraagd.', 'O boneco de treino não pediu nada.'),
    'spell_intro': T('Le maître de classe approuve.', 'Your class master approves.', 'Dein Klassenmeister ist zufrieden.', 'Tu maestro de clase lo aprueba.', 'Il tuo maestro di classe approva.', 'Je klassenmeester keurt het goed.', 'O teu mestre de classe aprova.'),
}
for k, j in UJOKE.items():
    for lg in C['ui']:
        if k in C['ui'][lg] and lg in j: C['ui'][lg][k] = C['ui'][lg][k] + ' ' + j[lg]
TIPS = [
    T('Les Tofus ne sont pas méchants. Juste très, très nombreux.', 'Tofus aren\'t mean. Just very, very numerous.', 'Tofus sind nicht böse. Nur sehr, sehr zahlreich.', 'Los Tofus no son malos. Solo muy, muy numerosos.', 'I Tofu non sono cattivi. Solo molto, molto numerosi.', 'Tofu\'s zijn niet gemeen. Alleen heel, heel talrijk.', 'Os Tofus não são maus. Só muito, muito numerosos.'),
    T('Un Iop a essayé de réfléchir, une fois. On l\'attend encore.', 'An Iop tried to think once. We\'re still waiting.', 'Ein Iop hat einmal versucht nachzudenken. Wir warten noch.', 'Un Iop intentó pensar una vez. Aún lo esperamos.', 'Un Iop ha provato a pensare, una volta. Lo aspettiamo ancora.', 'Een Iop probeerde ooit na te denken. We wachten nog steeds.', 'Um Iop tentou pensar, uma vez. Ainda estamos à espera.'),
    T('Ne faites jamais confiance à un coffre qui sourit.', 'Never trust a chest that smiles.', 'Trau nie einer Truhe, die lächelt.', 'Nunca te fíes de un cofre que sonríe.', 'Mai fidarsi di un forziere che sorride.', 'Vertrouw nooit een kist die glimlacht.', 'Nunca confies num baú que sorri.'),
    T('Le Tofu Mutant court plus vite que vous. Sauf si vous courez plus vite.', 'The Mutant Tofu runs faster than you. Unless you run faster.', 'Der Mutanten-Tofu ist schneller als du. Außer du bist schneller.', 'El Tofu Mutante corre más que tú. Salvo si corres más.', 'Il Tofu Mutante corre più di te. A meno che tu non corra di più.', 'De Mutantentofu is sneller dan jij. Tenzij jij sneller bent.', 'O Tofu Mutante corre mais do que tu. A não ser que corras mais.'),
    T('Musha l\'Oni perd des cartes au trésor. Rien de louche, voyons.', 'Musha the Oni loses treasure maps. Nothing fishy, of course.', 'Oni Musha verliert Schatzkarten. Nichts Verdächtiges, natürlich.', 'Musha el Oni pierde mapas del tesoro. Nada sospechoso, claro.', 'Musha l\'Oni perde mappe del tesoro. Niente di losco, ovvio.', 'Musha de Oni verliest schatkaarten. Niets verdachts, natuurlijk.', 'O Musha o Oni perde mapas do tesouro. Nada de suspeito, claro.'),
    T('La roue du Trool est truquée. Mais gentiment.', 'The Trool wheel is rigged. But kindly.', 'Das Trool-Rad ist manipuliert. Aber nett.', 'La rueda del Trool está trucada. Pero con cariño.', 'La ruota del Trool è truccata. Ma gentilmente.', 'Het Troolrad is vervalst. Maar vriendelijk.', 'A roda do Trool está viciada. Mas com carinho.'),
    T('Les Maîtres Corbacs n\'ont jamais entendu parler de la pause.', 'The Crobak Masters never heard of breaks.', 'Die Korback-Meister kennen keine Pause.', 'Los Maestros Corbac nunca oyeron hablar de pausas.', 'I Maestri Corbac non hanno mai sentito parlare di pause.', 'De Meesterkraaiers hebben nooit van pauze gehoord.', 'Os Mestres Corbac nunca ouviram falar de pausas.'),
    T('Un Enutrof ne perd jamais rien : il range ailleurs.', 'An Enutrof never loses anything: he stores it elsewhere.', 'Ein Enutrof verliert nie etwas: Er räumt es woanders hin.', 'Un Anutrof nunca pierde nada: lo guarda en otro sitio.', 'Un Enutrof non perde mai niente: lo mette altrove.', 'Een Enutrof verliest nooit iets: hij legt het ergens anders.', 'Um Enutrof nunca perde nada: arruma noutro sítio.'),
    T('Le mode Difficile ? Le crâne de Crâ vous juge déjà.', 'Hard mode? The Cra skull is already judging you.', 'Schwer-Modus? Der Cra-Schädel urteilt schon über dich.', '¿Modo Difícil? El cráneo de Ocra ya te juzga.', 'Modalità Difficile? Il teschio di Cra ti sta già giudicando.', 'Moeilijke modus? De Cra-schedel oordeelt al over je.', 'Modo Difícil? O crânio de Cra já te está a julgar.'),
    T('Les Archimonstres ont des noms à rallonge. Leurs âmes aussi.', 'Archmonsters have very long names. So do their souls.', 'Erzmonster haben ellenlange Namen. Ihre Seelen auch.', 'Los Archimonstruos tienen nombres larguísimos. Sus almas también.', 'Gli Arcimostri hanno nomi lunghissimi. Anche le loro anime.', 'Aartsmonsters hebben ellenlange namen. Hun zielen ook.', 'Os Arquimonstros têm nomes compridíssimos. As almas também.'),
]
for t in TIPS:
    for lg in C['tips']:
        if t[lg] not in C['tips'][lg]: C['tips'][lg].append(t[lg])

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.31 ok', len(C['achievements']), 'achievements')
