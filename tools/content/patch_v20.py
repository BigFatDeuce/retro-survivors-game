"""v2.0 content, applied on the published v1.9 content (work/content_v19.json) -> game/data/content.json.
Balance (monsters, first levels, attack speed ramp), spell shop, the real spell scrolls, profiles, new texts."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, json, os
import langdata as LD

G = f'{ROOT}/game'
C = json.load(open(f'{ROOT}/work/content_v19.json'))
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']


def T(*a): return dict(zip(LG, a))


# ---------------------------------------------------------------- balance
R = C['run']
R['hpMul'] = 1.15 * 1.15   # every monster +15% HP, then +15% again (v2.0.2)
R['meleeMul'] = 1.20       # melee blows +20%
R['rangedMul'] = 1.10      # ranged attacks +10%
R['xpEarly'] = [2.8, 2.8, 2.4, 1.9, 1.5, 1.25, 1.1]   # the first levels need more experience
R['cdEarly'] = 0.35        # cooldowns x1.35 at the start, back to normal at level 15 (or 2:30 at the latest)
R['cdEarlyT'] = 150
R['xpPace'] = 3.25         # (was 3.0) sturdier monsters die slower: a little more experience each
R['cdEarlyLv'] = 15
R['cdMul'] = 1 / 0.7        # v2.0.2: every spell and weapon of the player attacks 30% slower
R['dashMul'] = 1.15         # v2.0.2: spells that move the character (Bond, Assaut, Vol de Pièces) +15% damage
for k, v in json.loads(os.environ.get('RUNX', '{}')).items(): R[k] = v   # sim variants

# ---------------------------------------------------------------- the real spell scrolls (the items that teach the spells)
D = C['drops']
for k, iid in (('flamiche', 718), ('liberation', 719), ('foudre', 720)):
    info = LD.item_info(iid)
    D[k]['item'] = f"it_{info['t']}_{info['g']}"
    D[k]['itemName'] = LD.item(iid)
    D[k]['itemSize'] = 50
# the lang data gives Foudroiement the plain rolled scroll (gfx 3, like Libération); the client's own Foudroiement scroll is
# the yellow one with the lightning bolt (clips/items/75/19.swf)
D['foudre']['item'] = 'it_75_19'
# same for Libération: the generic rolled scroll in the lang data, its own scroll is the one with the gust of wind (75/18.swf),
# drawn like the Flamiche (75/1.swf, burnt) and Foudroiement ones
D['liberation']['item'] = 'it_75_18'

# ---------------------------------------------------------------- pets only known in French (no item in the lang files)
# Official names where they exist: DOFUS (api.dofusdb.fr: en, de, es, pt) and the Retro lang files (Tifoux Tigré, the Croum
# and Dragoune families); Italian and Dutch follow the Retro translations of the same family; names found nowhere are
# translated after the official ones of their family, proper names are kept.
PETN = {   # id: (en, de, es, it, nl, pt)
    '18_62': ('Komet', 'Kometh', 'Kometa', 'Kometh', 'Komet', 'Kometh'),
    '18_63': ('Armoured Dragoone', 'Gepanzerter Dragooner', 'Dragún con armadura', 'Dragona in Armatura', 'Gepantserde Dragoone', 'Draguna com Armadura'),
    '18_64': ('Red Dragoone', 'Roter Dragooner', 'Dragún rojo', 'Dragona Rossa', 'Rode Dragoone', 'Draguna Vermelha'),
    '18_66': ('Glutton', 'Vielfraß', 'Glotón', 'Ghiottone', 'Veelvraat', 'Glutão'),
    '18_67': ('Kwismas Reindeer', 'Weißnachtsrentier', 'Renito', 'Rennowel', 'Rennowel', 'Renataw'),
    '18_68': ('Weegle Owl', 'Miniduk', 'Minichuelo', 'Miniduk', 'Miniduk', 'Miniduk'),
    '18_70': ('Brindled Minifoux', 'Gescheckter Minifux', 'Pekefux atigrado', 'Tifux Tigrato', 'Gestreepte Minifoux', 'Raposa Malhada'),
    '18_71': ('Solar Bear', 'Polär', 'Polaroso', 'Orsolare', 'Zonnebeer', 'Ursolar'),
    '18_73': ('Tibilax', 'Tibilax', 'Pekebilax', 'Tibilax', 'Tibilax', 'Tibilax'),
    '18_75': ('Sapphire Tibilax', 'Tibilax-Saphir', 'Pekebilax zafiro', 'Tibilax Zaffiro', 'Saffier Tibilax', 'Tibilax Safira'),
    '18_76': ('Patrick the Sand Pie', 'Patrick der Sandkuchen', 'Patrick el flan de arena', 'Patrick la formina di sabbia', 'Patrick de zandtaart', 'Patrick, o Bolo de Areia'),
    '18_78': ('Karne', 'Däschel', 'Karne', 'Karne', 'Karne', 'Karne'),
    '18_79': ("Cire's Hand", 'Cires Hand', 'Mano de Cire', 'Mano di Cire', "Cire's Hand", 'Mão de Cire'),
    '18_85': ('Kourial', 'Kourial', 'Kurial', 'Kurial', 'Kourial', 'Kurial'),
    '18_87': ('Volatile Croum', 'Flüchtiger Croum', 'Crum volátil', 'Crum Volatile', 'Vluchtige Croum', 'Croo Volátil'),
    '18_88': ('Aqueous Croum', 'Croum der Fluten', 'Crum acuoso', 'Crum Acquoso', 'Waterige Croum', 'Croo Aquoso'),
    '18_89': ('Fiery Croum', 'Flammender Croum', 'Crum ígneo', 'Crum Igneo', 'Vurige Croum', 'Croo Ígneo'),
    '18_90': ('Verdant Croum', 'Pflanzlicher Croum', 'Crum vegetal', 'Crum Vegetale', 'Plantaardige Croum', 'Croo Vegetal'),
    '18_91': ('The Famystique', 'Der Famystique', 'El Famystique', 'Il Famystique', 'De Famystique', 'O Famystique'),
}
for p_ in C['pets']:
    if p_['id'] in PETN:
        p_['name'] = dict(fr=p_['name']['fr'], **dict(zip(['en', 'de', 'es', 'it', 'nl', 'pt'], PETN[p_['id']])))

# ---------------------------------------------------------------- spell shop: 5 levels per class spell, the price of the first 5 scroll levels
C['spellCost'] = C['scrollCost'][:5]
C['spellPer'] = 0.10

# ---------------------------------------------------------------- texts
UI = {
    'profiles': T('Profils', 'Profiles', 'Profile', 'Perfiles', 'Profili', 'Profielen', 'Perfis'),
    'profile_n': T('Profil {n}', 'Profile {n}', 'Profil {n}', 'Perfil {n}', 'Profilo {n}', 'Profiel {n}', 'Perfil {n}'),
    'profile_info': T('{r} parties · {k} kamas · {a} succès', '{r} runs · {k} kamas · {a} achievements', '{r} Läufe · {k} Kamas · {a} Erfolge',
                      '{r} partidas · {k} kamas · {a} logros', '{r} partite · {k} kama · {a} obiettivi', '{r} runs · {k} kama\'s · {a} prestaties', '{r} partidas · {k} kamas · {a} conquistas'),
    'profile_empty': T('Vide — une nouvelle aventure', 'Empty — a new adventure', 'Leer — ein neues Abenteuer', 'Vacío — una nueva aventura', 'Vuoto — una nuova avventura', 'Leeg — een nieuw avontuur', 'Vazio — uma nova aventura'),
    'profile_current': T('Actuel', 'Current', 'Aktuell', 'Actual', 'Attuale', 'Huidig', 'Atual'),
    'profile_pick': T('Choisir', 'Select', 'Wählen', 'Elegir', 'Scegli', 'Kiezen', 'Escolher'),
    'profile_switched': T('Profil {n} chargé.', 'Profile {n} loaded.', 'Profil {n} geladen.', 'Perfil {n} cargado.', 'Profilo {n} caricato.', 'Profiel {n} geladen.', 'Perfil {n} carregado.'),
    'profiles_hint': T('Chaque profil a sa propre progression : kamas, achats, zones, succès, bestiaire et Dofus. Les réglages sont communs.',
                       'Each profile has its own progress: kamas, purchases, zones, achievements, bestiary and Dofus. Settings are shared.',
                       'Jedes Profil hat seinen eigenen Fortschritt: Kamas, Käufe, Zonen, Erfolge, Bestiarium und Dofus. Die Einstellungen sind gemeinsam.',
                       'Cada perfil tiene su propio progreso: kamas, compras, zonas, logros, bestiario y Dofus. Los ajustes son comunes.',
                       'Ogni profilo ha i propri progressi: kama, acquisti, zone, obiettivi, bestiario e Dofus. Le impostazioni sono condivise.',
                       'Elk profiel heeft zijn eigen voortgang: kama\'s, aankopen, zones, prestaties, bestiarium en Dofus. De instellingen zijn gedeeld.',
                       'Cada perfil tem o seu próprio progresso: kamas, compras, zonas, conquistas, bestiário e Dofus. As configurações são comuns.'),
    'reset_progress': T('Réinitialiser la progression', 'Reset progress', 'Fortschritt zurücksetzen', 'Reiniciar el progreso', 'Azzera i progressi', 'Voortgang resetten', 'Reiniciar o progresso'),
    'reset_confirm': T('Tout effacer ? Cliquez encore', 'Erase everything? Click again', 'Alles löschen? Nochmals klicken', '¿Borrarlo todo? Pulsa otra vez', 'Cancellare tutto? Clicca di nuovo', 'Alles wissen? Klik nogmaals', 'Apagar tudo? Clique de novo'),
    'reset_hint': T('Remet le profil {n} à zéro : kamas, achats, zones, succès, bestiaire, statistiques et Dofus. Impossible à annuler.',
                    'Resets profile {n} to zero: kamas, purchases, zones, achievements, bestiary, statistics and Dofus. This cannot be undone.',
                    'Setzt Profil {n} auf null zurück: Kamas, Käufe, Zonen, Erfolge, Bestiarium, Statistiken und Dofus. Nicht rückgängig zu machen.',
                    'Pone el perfil {n} a cero: kamas, compras, zonas, logros, bestiario, estadísticas y Dofus. No se puede deshacer.',
                    'Azzera il profilo {n}: kama, acquisti, zone, obiettivi, bestiario, statistiche e Dofus. Non si può annullare.',
                    'Zet profiel {n} terug op nul: kama\'s, aankopen, zones, prestaties, bestiarium, statistieken en Dofus. Kan niet ongedaan worden.',
                    'Reinicia o perfil {n}: kamas, compras, zonas, conquistas, bestiário, estatísticas e Dofus. Não pode ser desfeito.'),
    'reset_done': T('Progression remise à zéro. Bonne nouvelle aventure !', 'Progress reset. Have a good new adventure!', 'Fortschritt zurückgesetzt. Viel Spaß beim neuen Abenteuer!',
                    'Progreso reiniciado. ¡Buena nueva aventura!', 'Progressi azzerati. Buona nuova avventura!', 'Voortgang gereset. Veel plezier met je nieuwe avontuur!', 'Progresso reiniciado. Boa nova aventura!'),
    'spell_intro': T('Améliorez les sorts de chaque classe : +10 % de puissance (dégâts et soins) par niveau, 5 niveaux par sort. Valable pour toutes vos parties avec cette classe.',
                     'Upgrade every class spell: +10% power (damage and heals) per level, 5 levels per spell. Works in all your runs with that class.',
                     'Verbessere die Zauber jeder Klasse: +10 % Kraft (Schaden und Heilung) pro Stufe, 5 Stufen pro Zauber. Gilt für alle Läufe mit dieser Klasse.',
                     'Mejora los hechizos de cada clase: +10 % de poder (daño y curas) por nivel, 5 niveles por hechizo. Vale para todas tus partidas con esa clase.',
                     'Migliora gli incantesimi di ogni classe: +10% di potenza (danni e cure) per livello, 5 livelli per incantesimo. Vale per tutte le partite con quella classe.',
                     'Verbeter de spreuken van elke klasse: +10% kracht (schade en genezing) per niveau, 5 niveaus per spreuk. Geldt voor al je runs met die klasse.',
                     'Melhore os feitiços de cada classe: +10% de poder (dano e curas) por nível, 5 níveis por feitiço. Vale para todas as partidas com essa classe.'),
    'spell_lv': T('Niveau {n}/{m}', 'Level {n}/{m}', 'Stufe {n}/{m}', 'Nivel {n}/{m}', 'Livello {n}/{m}', 'Niveau {n}/{m}', 'Nível {n}/{m}'),
    'spell_bonus': T('+{n}% de puissance', '+{n}% power', '+{n} % Kraft', '+{n} % de poder', '+{n}% di potenza', '+{n}% kracht', '+{n}% de poder'),
    'fs_press': T('Appuyez sur une touche ou touchez l\'écran pour passer en plein écran.', 'Press a key or tap the screen to go fullscreen.', 'Drücke eine Taste oder tippe auf den Bildschirm für den Vollbildmodus.',
                  'Pulsa una tecla o toca la pantalla para pasar a pantalla completa.', 'Premi un tasto o tocca lo schermo per lo schermo intero.', 'Druk op een toets of tik op het scherm voor volledig scherm.', 'Prima uma tecla ou toque no ecrã para ecrã inteiro.'),
}
for k, v in UI.items():
    for lg in LG: C['ui'].setdefault(lg, {})[k] = v[lg]

# ---------------------------------------------------------------- achievements: a real item picture for every one, and 15 more
def IT(iid):
    i = LD.item_info(iid); return f"it_{i['t']}_{i['g']}"


ICONS = {
    'first_run': IT(297), 'runs_25': IT(127), 'runs_100': IT(129), 'kills_1k': IT(301), 'kills_10k': IT(2453), 'kills_100k': IT(481),
    'run_kills_1000': IT(387), 'run_kills_2500': IT(2336), 'survive_5': 'hourglass', 'survive_10': IT(7372), 'first_win': IT(1331),
    'win_5': IT(7070), 'win_all': IT(7921), 'secret': IT(1570), 'level_30': IT(2337), 'level_60': IT(969), 'kamas_10k': IT(8922),
    'kamas_100k': IT(10665), 'bosses_10': IT(7038), 'bosses_100': IT(8275), 'classes_all': IT(6986), 'no_hit_3': IT(2296),
    'revive': IT(1742), 'bestiary_half': IT(489), 'bestiary_all': IT(1626), 'doom_30': IT(1889),
}
DOF = {d['id']: 'it_23_' + str(d['icon']) for d in C['dofus']}
ICONS['dofus_1'] = DOF.get('emeraude') or list(DOF.values())[0]
ICONS['dofus_all'] = DOF.get('pourpre') or list(DOF.values())[-1]
ICONS['tot_win'] = DOF.get('ocre') or list(DOF.values())[1]
for a in C['achievements']:
    if a['id'] in ICONS: a['icon'] = ICONS[a['id']]
NEW = [
    ('spell_buy', 'spellBuys', 1, IT(731), T('Apprenti', 'Apprentice', 'Lehrling', 'Aprendiz', 'Apprendista', 'Leerling', 'Aprendiz'),
     T('Acheter un niveau de sort dans la boutique.', 'Buy a spell level in the shop.', 'Kaufe eine Zauberstufe im Laden.', 'Compra un nivel de hechizo en la tienda.', 'Compra un livello di incantesimo nel negozio.', 'Koop een spreukniveau in de winkel.', 'Compre um nível de feitiço na loja.')),
    ('spell_max', 'spellMaxed', 1, IT(6664), T('Sort maîtrisé', 'Spell mastered', 'Zauber gemeistert', 'Hechizo dominado', 'Incantesimo padroneggiato', 'Spreuk beheerst', 'Feitiço dominado'),
     T('Monter un sort au niveau 5 dans la boutique.', 'Raise a spell to level 5 in the shop.', 'Bringe einen Zauber im Laden auf Stufe 5.', 'Sube un hechizo al nivel 5 en la tienda.', 'Porta un incantesimo al livello 5 nel negozio.', 'Breng een spreuk naar niveau 5 in de winkel.', 'Leve um feitiço ao nível 5 na loja.')),
    ('spell_class', 'spellClassMax', 1, IT(410), T('Grimoire complet', 'Complete grimoire', 'Vollständiges Zauberbuch', 'Grimorio completo', 'Grimorio completo', 'Compleet toverboek', 'Grimório completo'),
     T('Monter tous les sorts d\'une classe au niveau 5.', 'Raise every spell of a class to level 5.', 'Bringe alle Zauber einer Klasse auf Stufe 5.', 'Sube todos los hechizos de una clase al nivel 5.', 'Porta tutti gli incantesimi di una classe al livello 5.', 'Breng alle spreuken van een klasse naar niveau 5.', 'Leve todos os feitiços de uma classe ao nível 5.')),
    ('mastery_max', 'masteryMax', 1, IT(7136), T('Maître d\'armes', 'Weapon master', 'Waffenmeister', 'Maestro de armas', 'Maestro d\'armi', 'Wapenmeester', 'Mestre de armas'),
     T('Monter une maîtrise d\'arme au niveau 10.', 'Raise a weapon mastery to level 10.', 'Bringe eine Waffenbeherrschung auf Stufe 10.', 'Sube una maestría de arma al nivel 10.', 'Porta una maestria d\'arma al livello 10.', 'Breng een wapenbeheersing naar niveau 10.', 'Leve uma maestria de arma ao nível 10.')),
    ('scroll_max', 'scrollMax', 1, IT(10513), T('Parchemineur', 'Scroll sage', 'Schriftrollen-Weiser', 'Sabio de pergaminos', 'Saggio delle pergamene', 'Perkamentwijze', 'Sábio dos pergaminhos'),
     T('Monter un parchemin de caractéristique au niveau 10.', 'Raise a characteristic scroll to level 10.', 'Bringe eine Eigenschaftsschriftrolle auf Stufe 10.', 'Sube un pergamino de característica al nivel 10.', 'Porta una pergamena di caratteristica al livello 10.', 'Breng een eigenschapsrol naar niveau 10.', 'Leve um pergaminho de característica ao nível 10.')),
    ('elites_50', 'elites', 50, IT(2246), T('Chasseur d\'élites', 'Elite hunter', 'Elitejäger', 'Cazador de élites', 'Cacciatore d\'élite', 'Elitejager', 'Caçador de elites'),
     T('Vaincre 50 monstres d\'élite.', 'Defeat 50 elite monsters.', 'Besiege 50 Elitemonster.', 'Derrota a 50 monstruos de élite.', 'Sconfiggi 50 mostri d\'élite.', 'Versla 50 elitemonsters.', 'Derrote 50 monstros de elite.')),
    ('chests_25', 'chests', 25, IT(2040), T('Pilleur de coffres', 'Chest looter', 'Truhenplünderer', 'Saqueador de cofres', 'Saccheggiatore di forzieri', 'Kistenplunderaar', 'Saqueador de baús'),
     T('Ouvrir 25 coffres.', 'Open 25 chests.', 'Öffne 25 Truhen.', 'Abre 25 cofres.', 'Apri 25 forzieri.', 'Open 25 kisten.', 'Abra 25 baús.')),
    ('breads_50', 'breads', 50, IT(524), T('Boulanger fidèle', 'Loyal customer', 'Treuer Kunde', 'Cliente fiel', 'Cliente fedele', 'Trouwe klant', 'Cliente fiel'),
     T('Manger 50 pains.', 'Eat 50 loaves of bread.', 'Iss 50 Brote.', 'Come 50 panes.', 'Mangia 50 pagnotte.', 'Eet 50 broden.', 'Coma 50 pães.')),
    ('crits_1k', 'crits', 1000, IT(395), T('Coups de chance', 'Lucky strikes', 'Glückstreffer', 'Golpes de suerte', 'Colpi fortunati', 'Gelukstreffers', 'Golpes de sorte'),
     T('Infliger 1 000 coups critiques.', 'Land 1,000 critical hits.', 'Lande 1.000 kritische Treffer.', 'Asesta 1000 golpes críticos.', 'Infliggi 1.000 colpi critici.', 'Deel 1.000 kritieke treffers uit.', 'Acerte 1.000 golpes críticos.')),
    ('best_hit_1k', 'bestHit', 1000, IT(620), T('Coup de maître', 'Masterstroke', 'Meisterschlag', 'Golpe maestro', 'Colpo da maestro', 'Meesterslag', 'Golpe de mestre'),
     T('Infliger 1 000 dégâts en un seul coup.', 'Deal 1,000 damage in a single hit.', 'Verursache 1.000 Schaden mit einem Treffer.', 'Inflige 1000 de daño de un solo golpe.', 'Infliggi 1.000 danni in un solo colpo.', 'Deel 1.000 schade uit met één slag.', 'Cause 1.000 de dano num só golpe.')),
    ('playtime_5h', 'playtime', 18000, IT(2311), T('Noctambule', 'Night owl', 'Nachteule', 'Noctámbulo', 'Nottambulo', 'Nachtuil', 'Notívago'),
     T('Jouer 5 heures au total.', 'Play for 5 hours in total.', 'Spiele insgesamt 5 Stunden.', 'Juega 5 horas en total.', 'Gioca 5 ore in totale.', 'Speel in totaal 5 uur.', 'Jogue 5 horas no total.')),
    ('tailor_win', 'tailor', 1, C['manuel']['icon'], T('Tailleur chanceux', 'Lucky tailor', 'Glücklicher Schneider', 'Sastre afortunado', 'Sarto fortunato', 'Gelukkige kleermaker', 'Alfaiate sortudo'),
     T('Gagner au Manuel du Tailleur.', 'Win at the Tailor\'s Manual.', 'Gewinne beim Schneiderhandbuch.', 'Gana con el Manual del Sastre.', 'Vinci col Manuale del Sarto.', 'Win bij het Kleermakershandboek.', 'Ganhe com o Manual do Alfaiate.')),
    ('majeure', 'majeure', 1, C['drops']['arakne']['item'], T('Reine des araignées', 'Spider queen', 'Spinnenkönigin', 'Reina de las arañas', 'Regina dei ragni', 'Spinnenkoningin', 'Rainha das aranhas'),
     T('Invoquer l\'Arakne Majeure.', 'Summon the Major Arachnee.', 'Beschwöre die Große Arakne.', 'Invoca a la Arakna Mayor.', 'Evoca l\'Arakne Maggiore.', 'Roep de Grote Arakne op.', 'Invoque a Aranha Maior.')),
    ('gems_10k', 'gems', 10000, C['ambers'][1], T('Collectionneur d\'ambre', 'Amber collector', 'Bernsteinsammler', 'Coleccionista de ámbar', 'Collezionista d\'ambra', 'Barnsteenverzamelaar', 'Colecionador de âmbar'),
     T('Ramasser 10 000 ambres.', 'Pick up 10,000 ambers.', 'Sammle 10.000 Bernsteine.', 'Recoge 10.000 ámbares.', 'Raccogli 10.000 ambre.', 'Raap 10.000 barnstenen op.', 'Apanhe 10.000 âmbares.')),
    ('globetrotter', 'dist', 600000, IT(959), T('Globe-trotteur', 'Globetrotter', 'Weltenbummler', 'Trotamundos', 'Giramondo', 'Wereldreiziger', 'Globetrotter'),
     T('Parcourir 10 000 cases.', 'Travel 10,000 cells.', 'Lege 10.000 Felder zurück.', 'Recorre 10.000 casillas.', 'Percorri 10.000 caselle.', 'Leg 10.000 vakjes af.', 'Percorra 10.000 casas.')),
]
have = {a['id'] for a in C['achievements']}
for aid, k, n, icon, name, desc in NEW:
    if aid not in have: C['achievements'].append(dict(id=aid, k=k, n=n, icon=icon, name=name, desc=desc))

# ---------------------------------------------------------------- the new zone (the shipwreck island; Moon was dropped)
import newzones20 as NZ
NZ.apply(C)
for m in C['maps']:
    if m['id'] == 'naufrages': m['lvl'] = '10 - 95'
nvis = sum(1 for m in C['maps'] if not m.get('hidden'))
for a in C['achievements']:
    if a['id'] == 'win_all':
        old = a['n']; a['n'] = nvis
        a['desc'] = {lg: v.replace(str(old), str(nvis)) for lg, v in a['desc'].items()}

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('v20 ok', {k: R[k] for k in ('hpMul', 'meleeMul', 'rangedMul', 'cdEarly')}, {k: D[k]['item'] for k in ('flamiche', 'liberation', 'foudre')})
