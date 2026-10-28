"""0.95 content, on top of patch_094:
- shields: the Primordial ones go except the Bricoleur's (82_57), the Polykrome ones go (no Polykrome skin is left in any
  slot); they join C.removedSkins (bought ones refunded at boot, main.js); the shields sorted by price like the others
- Démultiplication (`invocations`) offered half as often at level-up: `offerK` 0.5 (game.js upgradeOptions)
- the Tofuzmo (a.k.a. 'Tofukaze'): 1 000 HP (C.mutant.hp); from the zone after the 10th (C.maps index >= 10) Jorbak
  (client monster 2772, sprite 8038) comes instead: C.monsters.jorbak + C.jorbak (3 000 HP, keeps 10-15 m from the
  player, pushes him away like Libération with his 'Kleptomanie psychopathe' when closer than 1 m, a 15 % bonus, the only
  source of treasure maps: 25 % on his death: later: 50 %)
- treasure maps: no more random drop per run (C.tmap.chance 0) and the Maîtres Corbacs give the Manuel only (events.js)
- the Arakne majeure (the Arakne Agressive's pick-up): one push per summon, three times as far (`knock` x3, `pushOnce`)
- Endless: the final bosses' Manuel du Tailleur (was 50 % — 10 % x manuelK 5): 5 % from 10:00, +2.5 % per minute
  after (11:00 7.5 %, 12:00 10 %…): C.infinite.manuelP / manuelStep, read at the kill (game.js bossDeath)
- C.beginnerAid: the first three zones in Normal, until won there in Normal: monsters' HP x0.7 / 0.8 / 0.9, their blows x0.5
- C.gany: Ganymède (client NPC 378, sprite 9059 — the eagle-headed guide of Incarnam, `9059_z60` by build_npc57) and his
  scenes: the tutorial of each of the first three zones, and the Hard mode unlocked (Grobe won)
- strings: aid_info, hard_locked, jorbak_*, mutant_appears (1000 HP); the options' opt_fx* (visual effects) and
  opt_zoom* (camera distance)
- C.update + upd_*: the installed builds look for a newer release of the public repository (ui_update.js)
usage: python tools/make_content.py   (runs the newest patch; this one imports patch_094 and writes game/data/content.json)"""
import sys as _sys, os as _os, json
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import patch_094 as P

C, G, T, put_ui = P.C, P.G, P.T, P.put_ui
LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt']
lang = lambda kind: {lg: json.load(open(f'{_root.ROOT}/work/lang_json/{kind}_{lg}.json', encoding='utf-8')) for lg in LG}

# ---------------------------------------------------------------- shields
gone = [s for s in C['shields'] if ('Primordial' in s['name']['fr'] and s['id'] != '82_57') or 'Polykrome' in s['name']['fr']]
assert len(gone) == 35, len(gone)
for s in gone: C['removedSkins'][s['id']] = s['price']
C['shields'] = sorted([s for s in C['shields'] if s not in gone], key=lambda s: s['price'])   # (stable: same order within a price)
for k in ('hats', 'capes', 'pets', 'shields'):
    assert not any('olykrom' in v.lower() for it in C[k] for v in it['name'].values() if v), k

# ---------------------------------------------------------------- Démultiplication, half as often
next(p for p in C['passives'] if p['id'] == 'invocations')['offerK'] = 0.5

# ---------------------------------------------------------------- the Tofuzmo, Jorbak
C['mutant']['hp'] = 1000
for lg in LG: C['ui'][lg]['mutant_appears'] = C['ui'][lg]['mutant_appears'].replace('3500', '1000')
assert all('1000' in C['ui'][lg]['mutant_appears'] for lg in LG)
MON, SPL = lang('monsters'), lang('spells')
jname = {lg: MON[lg]['M']['2772'].get('n') or 'Jorbak' for lg in LG}
klepto = {lg: SPL[lg]['S']['1741'].get('n') for lg in LG}
for lg in LG:   # (the Dutch lang file has the text 'null' there)
    if not klepto[lg] or klepto[lg] == 'null': klepto[lg] = 'Psychopathische kleptomanie' if lg == 'nl' else klepto['en']
TM = C['monsters']['tofu_mutant']
C['monsters']['jorbak'] = dict(id='jorbak', did=2772, gfx=8038, name=jname, hp=3000, dmg=TM['dmg'], speed=210, xp=TM['xp'] * 1.5, beh='keep',
                               size=14, atk=None, attacks=[klepto], colors=None, scale=1.15, kb=1.0, sprite='8038_z40', rz=3.2,
                               lore={'lv': [400, 440], 'hp': [5250, 6250]}, special=1, art='a8038',
                               flavor=T("Un vieux pickpocket au sac de bambou bourré de kamas qui ne sont pas à lui. Il garde ses distances : si on l'approche, il vous envoie valser.",
                                        "An old pickpocket with a bamboo pack stuffed with kamas that aren't his. He keeps his distance: come too close and he sends you flying.",
                                        "Ein alter Taschendieb mit einer Bambuskiepe voller Kamas, die ihm nicht gehören. Er hält Abstand: Kommt man ihm zu nah, schleudert er einen davon.",
                                        "Un viejo carterista con una mochila de bambú repleta de kamas que no son suyos. Guarda las distancias: si te acercas, te manda por los aires.",
                                        "Un vecchio borseggiatore con una gerla di bambù piena di kama non suoi. Tiene le distanze: se ti avvicini, ti fa volare via.",
                                        "Een oude zakkenroller met een bamboe draagmand vol kama's die niet van hem zijn. Hij houdt afstand: kom je te dichtbij, dan slingert hij je weg.",
                                        "Um velho carteirista com um cesto de bambu cheio de kamas que não são dele. Mantém as distâncias: se te aproximas, manda-te pelos ares."))
# 1 m = 45 world units (about a third of the character's height drawn on screen): keep 10-15 m, push under 1 m
C['jorbak'] = {'from': 10, 'hp': 3000, 'keep': [450, 675], 'near': 45, 'cd': 2.5, 'push': 520, 'tmap': 0.5, 'buff': 0.15, 'spell': klepto, 'fx': 707, 'snd': 'punch'}
put_ui({
    'jorbak_appears': T("Jorbak rôde dans la zone avec son sac plein de kamas volés ! Attrapez-le avant qu'il ne file ({hp} PV) !",
                        "Jorbak is prowling the zone with his bag of stolen kamas! Catch him before he runs off ({hp} HP)!",
                        "Jorbak schleicht mit seinem Sack voll gestohlener Kamas durch die Zone! Fang ihn, bevor er abhaut ({hp} LP)!",
                        "¡Jorbak merodea por la zona con su saco lleno de kamas robados! ¡Atrápalo antes de que huya ({hp} PV)!",
                        "Jorbak si aggira nella zona con il suo sacco pieno di kama rubati! Prendilo prima che fugga ({hp} PV)!",
                        "Jorbak sluipt rond in de zone met zijn zak vol gestolen kama's! Vang hem voor hij ervandoor gaat ({hp} LP)!",
                        "Jorbak anda pela zona com o saco cheio de kamas roubados! Apanha-o antes que fuja ({hp} PV)!"),
    'jorbak_down': T('Jorbak vaincu : +{p} % {b} pour cette partie !', 'Jorbak defeated: +{p}% {b} for this run!', 'Jorbak besiegt: +{p} % {b} für diesen Lauf!',
                     'Jorbak vencido: ¡+{p} % {b} en esta partida!', 'Jorbak sconfitto: +{p}% {b} per questa partita!', 'Jorbak verslagen: +{p}% {b} voor deze run!', 'Jorbak derrotado: +{p}% {b} nesta partida!'),
    'jorbak_escaped': T("Jorbak a filé avec son butin. Il reviendra, il revient toujours.", "Jorbak ran off with his loot. He'll be back, he always is.",
                        "Jorbak ist mit seiner Beute abgehauen. Er kommt wieder, das tut er immer.", "Jorbak se largó con su botín. Volverá, siempre vuelve.",
                        "Jorbak è scappato con il bottino. Tornerà, torna sempre.", "Jorbak is er met zijn buit vandoor. Hij komt terug, dat doet hij altijd.",
                        "Jorbak fugiu com o saque. Há de voltar, volta sempre."),
})

# ---------------------------------------------------------------- treasure maps: Jorbak only
C['tmap']['chance'] = 0   # (no more random map drop per run; the Maîtres Corbacs give the Manuel only: events.js doomReward)

# ---------------------------------------------------------------- Endless: the final bosses' Manuel, 5 % + 2.5 % per minute after 10:00
C['infinite'].pop('manuelK', None); C['infinite']['manuelP'] = 0.05; C['infinite']['manuelStep'] = 0.025

# ---------------------------------------------------------------- the Arakne majeure: one push, three times as far
AM = C['drops']['arakne']['majeure']; AM['knock'] = AM['knock'] * 3; AM['pushOnce'] = 1

# ---------------------------------------------------------------- the beginners' help on the first three zones
C['beginnerAid'] = {'astrub': {'hp': 0.7, 'dmg': 0.5}, 'bonta': {'hp': 0.8, 'dmg': 0.5}, 'chafer': {'hp': 0.9, 'dmg': 0.5}}
assert [m['id'] for m in C['maps'][:3]] == list(C['beginnerAid'])
put_ui({
    'aid_info': T("🌱 {g} a demandé aux monstres de {map} d'y aller mollo : -{h} % de PV et -{d} % de dégâts, jusqu'à votre première victoire ici en difficulté Normale.",
                  "🌱 {g} asked the monsters of {map} to go easy on you: -{h}% HP and -{d}% damage, until your first win here in Normal.",
                  "🌱 {g} hat die Monster von {map} gebeten, sachte zu machen: -{h} % LP und -{d} % Schaden, bis zu deinem ersten Sieg hier auf Normal.",
                  "🌱 {g} pidió a los monstruos de {map} que se lo tomen con calma: -{h} % de PV y -{d} % de daño, hasta tu primera victoria aquí en Normal.",
                  "🌱 {g} ha chiesto ai mostri di {map} di andarci piano: -{h}% PV e -{d}% danni, fino alla tua prima vittoria qui in Normale.",
                  "🌱 {g} heeft de monsters van {map} gevraagd het rustig aan te doen: -{h}% LP en -{d}% schade, tot je eerste overwinning hier op Normaal.",
                  "🌱 {g} pediu aos monstros de {map} para irem com calma: -{h}% de PV e -{d}% de dano, até à tua primeira vitória aqui no Normal."),
    'hard_locked': T('🔒 Battez {map} pour débloquer le mode Difficile.', '🔒 Beat {map} to unlock Hard mode.', '🔒 Besiege {map}, um den Modus Schwer freizuschalten.',
                     '🔒 Supera {map} para desbloquear el modo Difícil.', '🔒 Supera {map} per sbloccare la modalità Difficile.', '🔒 Versla {map} om de modus Moeilijk te ontgrendelen.',
                     '🔒 Vence {map} para desbloquear o modo Difícil.'),
})

# ---------------------------------------------------------------- Ganymède and his scenes
NPC = lang('npc')
C['gany'] = {
    'sprite': '9059_z60', 'name': {lg: NPC[lg]['N']['d']['378']['n'] for lg in LG}, 'unlockHard': 'grobe',
    # each line: the text ({g} his name, {map} the zone, {b} its final boss, {p} the zone before's final boss, {h} / {d} the
    # zone's help in %, {v} Dark Vlad); his gesture per line is picked by ui_events.js
    'scenes': {
        'astrub': [
            T("Tiens, une nouvelle âme ! Tout juste descendue d'Incarnam, hein ? Je suis {g}. Écoute bien, je ne répéterai pas… enfin si, à chaque fois que tu mourras.",
              "Well, a new soul! Fresh down from Incarnam, eh? I'm {g}. Listen carefully, I won't repeat myself… well, I will, every time you die.",
              "Sieh an, eine neue Seele! Frisch aus Incarnam herabgestiegen, was? Ich bin {g}. Hör gut zu, ich wiederhole mich nicht … na gut, jedes Mal, wenn du stirbst.",
              "¡Vaya, un alma nueva! Recién bajada de Incarnam, ¿eh? Soy {g}. Escucha bien, no lo repetiré… bueno, sí, cada vez que mueras.",
              "Toh, un'anima nuova! Appena scesa da Incarnam, eh? Io sono {g}. Ascolta bene, non lo ripeterò… beh, sì, ogni volta che morirai.",
              "Kijk eens aan, een nieuwe ziel! Net neergedaald uit Incarnam, hè? Ik ben {g}. Luister goed, ik herhaal het niet… nou ja, wel, elke keer dat je doodgaat.",
              "Ora, uma alma nova! Acabada de descer de Incarnam, hein? Eu sou {g}. Ouve bem, não vou repetir… bom, vou, sempre que morreres."),
            T("Ici, c'est simple : les monstres arrivent par vagues, et toi, tu survis. Tes sorts se lancent tout seuls : toi, tu bouges et tu esquives.",
              "It's simple here: monsters come in waves, and you survive. Your spells cast themselves: you move and you dodge.",
              "Hier ist es einfach: Die Monster kommen in Wellen, und du überlebst. Deine Zauber wirken von selbst – du bewegst dich und weichst aus.",
              "Aquí es sencillo: los monstruos llegan en oleadas y tú sobrevives. Tus hechizos se lanzan solos: tú te mueves y esquivas.",
              "Qui è semplice: i mostri arrivano a ondate e tu sopravvivi. I tuoi incantesimi partono da soli: tu ti muovi e schivi.",
              "Het is hier simpel: de monsters komen in golven en jij overleeft. Je spreuken gaan vanzelf: jij beweegt en ontwijkt.",
              "Aqui é simples: os monstros chegam em vagas e tu sobrevives. Os teus feitiços lançam-se sozinhos: tu mexes-te e esquivas-te."),
            T("À chaque niveau, tu choisis : un nouveau sort, une arme, une caractéristique… Lis bien les cartes, elles disent ce que chaque attaque fait vraiment : dégâts, poison, poussée…",
              "Each level, you choose: a new spell, a weapon, a characteristic… Read the cards: they tell you what each attack really does — damage, poison, knockback…",
              "Mit jeder Stufe wählst du: einen neuen Zauber, eine Waffe, eine Eigenschaft … Lies die Karten genau, sie sagen dir, was jeder Angriff wirklich tut: Schaden, Gift, Rückstoß …",
              "En cada nivel eliges: un hechizo nuevo, un arma, una característica… Lee bien las cartas: dicen lo que hace de verdad cada ataque: daño, veneno, empuje…",
              "A ogni livello scegli: un nuovo incantesimo, un'arma, una caratteristica… Leggi bene le carte: dicono cosa fa davvero ogni attacco: danni, veleno, spinta…",
              "Elk level kies je: een nieuwe spreuk, een wapen, een eigenschap… Lees de kaarten goed: ze zeggen wat elke aanval echt doet: schade, gif, terugslag…",
              "A cada nível escolhes: um feitiço novo, uma arma, uma característica… Lê bem as cartas: dizem o que cada ataque faz mesmo: dano, veneno, empurrão…"),
            T("Entre deux parties, file à la boutique : améliore tes sorts, achète des parchemins et renforce tes caractéristiques. Les kamas ne servent à rien dans ta poche.",
              "Between runs, head to the shop: upgrade your spells, buy scrolls and train your characteristics. Kamas do nothing sitting in your pocket.",
              "Zwischen zwei Partien ab in den Laden: Verbessere deine Zauber, kauf Schriftrollen und stärke deine Eigenschaften. Kamas in der Tasche bringen gar nichts.",
              "Entre partida y partida, pasa por la tienda: mejora tus hechizos, compra pergaminos y refuerza tus características. Los kamas no sirven de nada en el bolsillo.",
              "Tra una partita e l'altra, passa al negozio: potenzia gli incantesimi, compra pergamene e rinforza le caratteristiche. I kama in tasca non servono a niente.",
              "Ga tussen twee potjes naar de winkel: verbeter je spreuken, koop perkamenten en versterk je eigenschappen. Kama's in je zak doen niks.",
              "Entre partidas, passa pela loja: melhora os feitiços, compra pergaminhos e reforça as características. Os kamas no bolso não servem para nada."),
            T("Ton objectif ici : vaincre {b}. Il est gros, il est laineux, et il n'aime pas trop qu'on tonde ses cousins.",
              "Your goal here: defeat {b}. He's big, he's woolly, and he doesn't like it when people shear his cousins.",
              "Dein Ziel hier: Besiege {b}. Er ist groß, er ist wollig, und er mag es gar nicht, wenn man seine Vettern schert.",
              "Tu objetivo aquí: derrotar a {b}. Es grande, es lanudo y no le gusta nada que esquilen a sus primos.",
              "Il tuo obiettivo qui: sconfiggere {b}. È grosso, è lanoso e non gli piace affatto che si tosino i suoi cugini.",
              "Je doel hier: {b} verslaan. Hij is groot, hij is wollig en hij houdt er niet van als je zijn neven scheert.",
              "O teu objetivo aqui: derrotar {b}. É grande, é lanudo e não gosta nada que tosquiem os primos dele."),
            T("Et comme je suis de bonne humeur : sur cette carte, les monstres ont {h} % de points de vie en moins et infligent {d} % de dégâts en moins. Profites-en !",
              "And since I'm in a good mood: on this map, monsters have {h}% less HP and deal {d}% less damage. Make the most of it!",
              "Und weil ich gute Laune habe: Auf dieser Karte haben die Monster {h} % weniger LP und verursachen {d} % weniger Schaden. Nutze es aus!",
              "Y como estoy de buen humor: en este mapa, los monstruos tienen un {h} % menos de PV e infligen un {d} % menos de daño. ¡Aprovéchalo!",
              "E visto che sono di buon umore: su questa mappa i mostri hanno il {h}% di PV in meno e infliggono il {d}% di danni in meno. Approfittane!",
              "En omdat ik goedgehumeurd ben: op deze kaart hebben de monsters {h}% minder LP en doen ze {d}% minder schade. Maak er gebruik van!",
              "E como estou de bom humor: neste mapa, os monstros têm menos {h}% de PV e causam menos {d}% de dano. Aproveita!"),
        ],
        'bonta': [
            T("Bravo, {p} est tombé ! On en parle jusqu'à Astrub… surtout ses cousins laineux, qui ne t'enverront pas de carte de vœux.",
              "Well done, {p} has fallen! They're talking about it all the way to Astrub… especially his woolly cousins, who won't be sending you a greeting card.",
              "Bravo, {p} ist gefallen! Man spricht bis nach Astrub davon … vor allem seine wolligen Vettern, die dir bestimmt keine Grußkarte schicken.",
              "¡Bravo, {p} ha caído! Se habla de ello hasta en Astrub… sobre todo sus primos lanudos, que no te mandarán ninguna postal.",
              "Bravo, {p} è caduto! Se ne parla fino ad Astrub… soprattutto i suoi cugini lanosi, che non ti manderanno certo un biglietto d'auguri.",
              "Bravo, {p} is gevallen! Ze praten er tot in Astrub over… vooral zijn wollige neven, die je echt geen wenskaart sturen.",
              "Bravo, {p} caiu! Fala-se disso até em Astrub… sobretudo os primos lanudos dele, que não te vão mandar nenhum postal."),
            T("Mais il se passe des choses étranges dans {map} : des champignons poussent là où on n'en avait jamais vu. Et certains ont des jambes.",
              "But strange things are happening in {map}: mushrooms are growing where nobody has ever seen any. And some of them have legs.",
              "Aber in {map} geschehen seltsame Dinge: Dort wachsen Pilze, wo noch nie welche zu sehen waren. Und manche haben Beine.",
              "Pero en {map} pasan cosas raras: brotan setas donde nunca se habían visto. Y algunas tienen piernas.",
              "Ma a {map} succedono cose strane: spuntano funghi dove non se ne erano mai visti. E alcuni hanno le gambe.",
              "Maar in {map} gebeuren vreemde dingen: er groeien paddenstoelen waar ze nog nooit gezien zijn. En sommige hebben benen.",
              "Mas em {map} passam-se coisas estranhas: crescem cogumelos onde nunca ninguém os tinha visto. E alguns têm pernas."),
            T("D'où sortent-ils ? Aucune idée. Mais si j'étais toi, je ne les goûterais pas.", "Where do they come from? No idea. But if I were you, I wouldn't taste them.",
              "Woher sie kommen? Keine Ahnung. Aber an deiner Stelle würde ich sie nicht probieren.", "¿De dónde salen? Ni idea. Pero yo que tú no las probaría.",
              "Da dove vengono? Non ne ho idea. Ma fossi in te, non li assaggerei.", "Waar ze vandaan komen? Geen idee. Maar als ik jou was, zou ik ze niet proeven.",
              "De onde vêm? Não faço ideia. Mas se fosse a ti, não os provava."),
            T("Allez, encore un coup de pouce : ici, les monstres ont {h} % de points de vie en moins et infligent {d} % de dégâts en moins.",
              "Here's one more helping hand: on this map, monsters have {h}% less HP and deal {d}% less damage.",
              "Noch eine kleine Hilfe: Hier haben die Monster {h} % weniger LP und verursachen {d} % weniger Schaden.",
              "Venga, otra ayudita: aquí los monstruos tienen un {h} % menos de PV e infligen un {d} % menos de daño.",
              "Dai, ancora una mano: qui i mostri hanno il {h}% di PV in meno e infliggono il {d}% di danni in meno.",
              "Nog een steuntje in de rug: hier hebben de monsters {h}% minder LP en doen ze {d}% minder schade.",
              "Vá, mais uma ajudinha: aqui os monstros têm menos {h}% de PV e causam menos {d}% de dano."),
        ],
        'chafer': [
            T("Encore toi ? Et toujours en vie ! Félicitations, je commence presque à croire en toi.", "You again? And still alive! Congratulations, I'm almost starting to believe in you.",
              "Du schon wieder? Und immer noch am Leben! Glückwunsch, langsam glaube ich fast an dich.", "¿Tú otra vez? ¡Y sigues vivo! Enhorabuena, casi empiezo a creer en ti.",
              "Ancora tu? E ancora vivo! Complimenti, quasi comincio a credere in te.", "Jij weer? En nog steeds in leven! Gefeliciteerd, ik begin bijna in je te geloven.",
              "Tu outra vez? E ainda vivo! Parabéns, quase começo a acreditar em ti."),
            T("Mais c'est ma dernière aide. Après, il faudra te débrouiller tout seul, comme une grande âme.", "But this is my last bit of help. After that, you'll have to manage on your own, like a big soul.",
              "Aber das ist meine letzte Hilfe. Danach musst du allein zurechtkommen, wie eine große Seele.", "Pero es mi última ayuda. Después tendrás que apañártelas solo, como un alma mayor.",
              "Ma è il mio ultimo aiuto. Dopo dovrai cavartela da solo, come un'anima grande.", "Maar dit is mijn laatste hulp. Daarna moet je het zelf redden, als een grote ziel.",
              "Mas é a minha última ajuda. Depois vais ter de te desenrascar sozinho, como uma alma crescida."),
            T("Un dernier conseil : achète des parchemins avant de dépenser tes kamas en chapeaux. Un chapeau n'a jamais sauvé personne, idiot !",
              "One last piece of advice: buy scrolls before blowing your kamas on hats. A hat never saved anyone's life, you fool!",
              "Ein letzter Rat: Kauf Schriftrollen, bevor du deine Kamas für Hüte verprasst. Ein Hut hat noch nie jemandem das Leben gerettet, du Dummkopf!",
              "Un último consejo: compra pergaminos antes de gastarte los kamas en sombreros. Un sombrero nunca le ha salvado la vida a nadie, ¡so tonto!",
              "Un ultimo consiglio: compra pergamene prima di sprecare i tuoi kama in cappelli. Un cappello non ha mai salvato la vita a nessuno, sciocco!",
              "Nog één raad: koop perkamenten voor je je kama's aan hoeden verspilt. Een hoed heeft nog nooit iemands leven gered, sukkel!",
              "Um último conselho: compra pergaminhos antes de gastar os kamas em chapéus. Um chapéu nunca salvou a vida de ninguém, palerma!"),
            T("Allez, pour la route : sur cette carte, les monstres ont {h} % de points de vie en moins et infligent {d} % de dégâts en moins. Ensuite, plus de cadeaux !",
              "One for the road: on this map, monsters have {h}% less HP and deal {d}% less damage. After that, no more gifts!",
              "Und eins für unterwegs: Auf dieser Karte haben die Monster {h} % weniger LP und verursachen {d} % weniger Schaden. Danach gibt's keine Geschenke mehr!",
              "Y una para el camino: en este mapa, los monstruos tienen un {h} % menos de PV e infligen un {d} % menos de daño. Después, ¡se acabaron los regalos!",
              "E una per la strada: su questa mappa i mostri hanno il {h}% di PV in meno e infliggono il {d}% di danni in meno. Poi, niente più regali!",
              "Nog eentje voor onderweg: op deze kaart hebben de monsters {h}% minder LP en doen ze {d}% minder schade. Daarna geen cadeautjes meer!",
              "Mais uma para o caminho: neste mapa, os monstros têm menos {h}% de PV e causam menos {d}% de dano. Depois disso, acabaram-se os presentes!"),
        ],
        'hard': [
            T("{map} est tombée devant toi ! Je dois l'admettre : tu n'es plus vraiment une jeune âme.", "{map} has fallen before you! I have to admit it: you're not really a young soul anymore.",
              "{map} ist vor dir gefallen! Ich muss zugeben: Du bist keine junge Seele mehr.", "¡{map} ha caído ante ti! Tengo que admitirlo: ya no eres precisamente un alma joven.",
              "{map} è caduta davanti a te! Devo ammetterlo: non sei più proprio un'anima giovane.", "{map} is voor je gevallen! Ik moet het toegeven: je bent niet echt meer een jonge ziel.",
              "{map} caiu perante ti! Tenho de admitir: já não és propriamente uma alma jovem."),
            T("Tu as gagné le droit de souffrir davantage : le mode Difficile est débloqué !", "You've earned the right to suffer more: Hard mode is unlocked!",
              "Du hast dir das Recht verdient, mehr zu leiden: Der Modus Schwer ist freigeschaltet!", "Te has ganado el derecho a sufrir más: ¡el modo Difícil está desbloqueado!",
              "Ti sei guadagnato il diritto di soffrire di più: la modalità Difficile è sbloccata!", "Je hebt het recht verdiend om meer te lijden: de modus Moeilijk is ontgrendeld!",
              "Ganhaste o direito de sofrer mais: o modo Difícil está desbloqueado!"),
            T("Les monstres y sont plus solides, frappent plus fort et ne te feront aucun cadeau. Exactement ce que tu voulais, non ?",
              "The monsters there are tougher, hit harder and won't give you any gifts. Exactly what you wanted, right?",
              "Die Monster dort sind zäher, schlagen härter zu und schenken dir nichts. Genau das, was du wolltest, oder?",
              "Allí los monstruos son más resistentes, pegan más fuerte y no te regalarán nada. Justo lo que querías, ¿no?",
              "Lì i mostri sono più resistenti, colpiscono più forte e non ti faranno nessun regalo. Proprio quello che volevi, no?",
              "De monsters daar zijn taaier, slaan harder en geven je niets cadeau. Precies wat je wilde, toch?",
              "Lá os monstros são mais resistentes, batem com mais força e não te dão presentes nenhuns. Exatamente o que querias, não?"),
            T("Curieusement, {v} ne veut pas entendre parler du mode Difficile. Il doit avoir ses raisons… Va donc lui demander lesquelles.",
              "Oddly enough, {v} won't hear a word about Hard mode. He must have his reasons… Why don't you go and ask him which ones?",
              "Seltsamerweise will {v} vom Modus Schwer nichts hören. Er wird seine Gründe haben … Geh doch hin und frag ihn, welche.",
              "Curiosamente, {v} no quiere ni oír hablar del modo Difícil. Tendrá sus motivos… ¿Por qué no vas a preguntarle cuáles?",
              "Stranamente, {v} non vuole sentir parlare della modalità Difficile. Avrà le sue ragioni… Perché non vai a chiedergli quali?",
              "Vreemd genoeg wil {v} niets horen over de modus Moeilijk. Hij zal zijn redenen hebben… Ga hem maar eens vragen welke.",
              "Curiosamente, {v} não quer ouvir falar do modo Difícil. Deve ter as suas razões… Porque não lhe vais perguntar quais?"),
        ],
    },
}
put_ui({'gany_skip': T('Passer', 'Skip', 'Überspringen', 'Saltar', 'Salta', 'Overslaan', 'Saltar'),
        'hard_unlocked': T('Mode Difficile débloqué !', 'Hard mode unlocked!', 'Modus Schwer freigeschaltet!', '¡Modo Difícil desbloqueado!',
                           'Modalità Difficile sbloccata!', 'Modus Moeilijk ontgrendeld!', 'Modo Difícil desbloqueado!')})
# the bestiary's behaviour lines of the two mini-bosses ToT's door lets out (0.95: both listed in their zones);
# beh_keep takes {d0} {d1} (his distance in m), {s} (his spell), {b} (his bonus %), {m} (his treasure map chance %)
put_ui({'beh_roam': T("Erre en tous sens et frappe au contact ; au bout d'un moment, il s'enfuit : rattrapez-le pour un bonus jusqu'à la fin de la partie.",
                      'Wanders all over and hits on contact; after a while it runs off: catch it for a bonus until the end of the run.',
                      'Streift ziellos umher und trifft bei Berührung; nach einer Weile haut er ab: Fang ihn für einen Bonus bis zum Ende der Partie.',
                      'Deambula por todas partes y golpea al contacto; al cabo de un rato se escapa: atrápalo para obtener una bonificación hasta el final de la partida.',
                      "Vaga ovunque e colpisce al contatto; dopo un po' scappa: prendilo per un bonus fino alla fine della partita.",
                      'Zwerft alle kanten op en raakt bij aanraking; na een tijdje gaat hij ervandoor: vang hem voor een bonus tot het einde van het potje.',
                      'Vagueia por todo o lado e acerta ao contacto; ao fim de algum tempo foge: apanha-o para um bónus até ao fim da partida.'),
        'beh_keep': T("Garde ses distances ({d0} à {d1} m) et vous repousse avec sa {s} si vous l'approchez à moins d'un mètre ; au bout d'un moment, il s'enfuit. Abattu : +{b} % jusqu'à la fin de la partie et {m} % de chances de lâcher une carte au trésor.",
                      'Keeps his distance ({d0} to {d1} m) and throws you back with his {s} if you come within a metre; after a while he runs off. Beaten: +{b} % until the end of the run and a {m} % chance to drop a treasure map.',
                      'Hält Abstand ({d0} bis {d1} m) und schleudert dich mit seiner {s} zurück, wenn du ihm auf einen Meter nahe kommst; nach einer Weile haut er ab. Besiegt: +{b} % bis zum Ende der Partie und {m} % Chance auf eine Schatzkarte.',
                      'Guarda las distancias ({d0} a {d1} m) y te empuja con su {s} si te acercas a menos de un metro; al cabo de un rato huye. Derrotado: +{b} % hasta el final de la partida y {m} % de probabilidad de soltar un mapa del tesoro.',
                      "Tiene le distanze (da {d0} a {d1} m) e ti respinge con la sua {s} se ti avvicini a meno di un metro; dopo un po' scappa. Sconfitto: +{b} % fino alla fine della partita e {m} % di probabilità di lasciare una mappa del tesoro.",
                      'Houdt afstand ({d0} tot {d1} m) en slingert je weg met zijn {s} als je binnen een meter komt; na een tijdje gaat hij ervandoor. Verslagen: +{b} % tot het einde van het potje en {m} % kans op een schatkaart.',
                      'Mantém as distâncias ({d0} a {d1} m) e repele-te com a sua {s} se te aproximares a menos de um metro; ao fim de algum tempo foge. Derrotado: +{b} % até ao fim da partida e {m} % de probabilidade de largar um mapa do tesouro.')})
# the options (0.95: simple settings for low-end machines, three camera distances)
put_ui({'opt_fx': T('Effets visuels', 'Visual effects', 'Visuelle Effekte', 'Efectos visuales', 'Effetti visivi', 'Visuele effecten', 'Efeitos visuais'),
        'opt_fx_full': T('Complets', 'Full', 'Voll', 'Completos', 'Completi', 'Volledig', 'Completos'),
        'opt_fx_low': T('Réduits', 'Reduced', 'Reduziert', 'Reducidos', 'Ridotti', 'Beperkt', 'Reduzidos'),
        'opt_fx_min': T('Minimaux', 'Minimal', 'Minimal', 'Mínimos', 'Minimi', 'Minimaal', 'Mínimos'),
        'opt_fx_hint': T("Réduits : moins de particules et de lueurs. Minimaux : aussi sans ombres de monstres ni effets derrière le décor. Les zones d'attaque restent toujours visibles.",
                         'Reduced: fewer particles and glows. Minimal: also no monster shadows and no effects behind the scenery. Attack areas always stay visible.',
                         'Reduziert: weniger Partikel und Leuchten. Minimal: zusätzlich keine Monsterschatten und keine Effekte hinter der Kulisse. Angriffszonen bleiben immer sichtbar.',
                         'Reducidos: menos partículas y brillos. Mínimos: además sin sombras de monstruos ni efectos tras el decorado. Las zonas de ataque siempre se ven.',
                         'Ridotti: meno particelle e bagliori. Minimi: anche niente ombre dei mostri né effetti dietro lo scenario. Le zone d\'attacco restano sempre visibili.',
                         'Beperkt: minder deeltjes en gloed. Minimaal: ook geen monsterschaduwen en geen effecten achter het decor. Aanvalszones blijven altijd zichtbaar.',
                         'Reduzidos: menos partículas e brilhos. Mínimos: também sem sombras de monstros nem efeitos atrás do cenário. As zonas de ataque ficam sempre visíveis.'),
        'opt_zoom': T('Caméra', 'Camera', 'Kamera', 'Cámara', 'Telecamera', 'Camera', 'Câmara'),
        'opt_zoom_far': T('Éloignée', 'Far', 'Weit', 'Lejana', 'Lontana', 'Ver', 'Afastada'),
        'opt_zoom_normal': T('Normale', 'Normal', 'Normal', 'Normal', 'Normale', 'Normaal', 'Normal'),
        'opt_zoom_close': T('Proche', 'Close', 'Nah', 'Cercana', 'Vicina', 'Dichtbij', 'Próxima')})

# ---------------------------------------------------------------- the installed builds: a newer version on GitHub (ui_update.js)
C['update'] = {'repo': 'BigFatDeuce/retro-survivors-game', 'hours': 6}
put_ui({'upd_title': T('Nouvelle version disponible', 'New version available', 'Neue Version verfügbar', 'Nueva versión disponible', 'Nuova versione disponibile', 'Nieuwe versie beschikbaar', 'Nova versão disponível'),
        'upd_text': T('La version {v} est sortie ! (vous avez la {cur})', 'Version {v} is out! (you have {cur})', 'Version {v} ist da! (du hast {cur})', '¡Ya salió la versión {v}! (tienes la {cur})', 'È uscita la versione {v}! (hai la {cur})', 'Versie {v} is uit! (jij hebt {cur})', 'A versão {v} saiu! (tens a {cur})'),
        'upd_how': T("Téléchargez-la sur la page qui va s'ouvrir, puis remplacez l'ancienne. Vos sauvegardes sont gardées.", 'Download it from the page that opens, then replace the old one. Your saves are kept.', 'Lade sie auf der Seite herunter, die sich öffnet, und ersetze die alte. Deine Spielstände bleiben erhalten.', 'Descárgala en la página que se abrirá y reemplaza la antigua. Tus partidas guardadas se conservan.', 'Scaricala dalla pagina che si apre, poi sostituisci quella vecchia. I tuoi salvataggi restano.', 'Download hem op de pagina die opent en vervang de oude. Je opgeslagen spellen blijven bewaard.', 'Descarrega-a na página que vai abrir e substitui a antiga. Os teus jogos guardados ficam.'),
        'upd_get': T('Télécharger', 'Download', 'Herunterladen', 'Descargar', 'Scarica', 'Downloaden', 'Descarregar'),
        'upd_badge': T('Version {v} disponible', 'Version {v} available', 'Version {v} verfügbar', 'Versión {v} disponible', 'Versione {v} disponibile', 'Versie {v} beschikbaar', 'Versão {v} disponível')})

# a TTG card's Portuguese name read as the text 'null' from the client: the English one instead
for c in C['ttg']['cards']:
    for lg, v in list(c['name'].items()):
        if v == 'null': c['name'][lg] = c['name'].get('en') or c['name'].get('fr')

# ---------------------------------------------------------------- 0.95, second list
# the Brigandin's passive: +10 % kamas instead of +30 % (Run.recompute adds passiveStats.greed to the 1.0 base)
BA = next(c for c in C['classes'] if c['id'] == 'bandit'); BA['passiveStats']['greed'] = 0.1
for lg in LG: assert '30' in BA['passive'][lg], lg; BA['passive'][lg] = BA['passive'][lg].replace('30', '10', 1)
# the Enutrof: base move speed +5 % (1.03 -> 1.0815; the speed bonuses still add to it, Run.recompute)
EN = next(c for c in C['classes'] if c['id'] == 'enutrof'); EN['base']['speed'] = round(EN['base']['speed'] * 1.05, 4)
# Lancer de Pièces: the coins' fan 30 % narrower (spread 0.5 -> 0.35 rad on each side), the cooldown -30 % (1.357 ->
# 0.95 s), then the throws faster level after level up to +50 % at the top (x1, x1.15, x1.3, x1.5: 0.95 / 0.826 / 0.731
# / 0.633 s). Its fusion fu_enu_pioche keeps its own numbers.
LP = C['spells']['lancer_pieces']; LP['base']['spread'] = 0.35; LP['base']['cd'] = round(1.357 * 0.7, 3)
for i, k in ((1, 1.15), (2, 1.3), (3, 1.5)): LP['lv'][i]['cd'] = round(LP['base']['cd'] / k, 3)
assert LP['base']['cd'] == 0.95 and [LP['lv'][i]['cd'] for i in (1, 2, 3)] == [0.826, 0.731, 0.633]
# weapons offered more often at level-up: game.js upgradeOptions (weights x1.3, measured: about +25 % of the level-ups show one)

# the Pwout de Cawotte + Cawotte fusion (any class: both are global spells, cls None; gspells.js pwcawotte). From the two
# spells at their top level: the Pwout's cloud (radius 120, a tick every 0.35 s, 4 s, every 5.252 s) in red-brown, twice
# its cawottes, following the character; it heals him like the Cawotte: as much per minute as the Cawotte gives at the
# same shop level when stood in (1.2 HP/s x 5.5 s every 25 s -> 2.0 x 8.5 every 18 with the whole shop), spread over the
# cloud's 4 s out of 5.252; four Cawottes (the Cawotte's zone and sprite, radius 70) around him hurt the monsters too.
# One group: a monster under two of its areas is hit once a tick.
PW, CW = C['spells']['prouts'], C['spells']['cawotte']
pw = dict(PW['base']); [pw.update(l) for l in PW['lv']]; cw = dict(CW['base']); [cw.update(l) for l in CW['lv']]
up = pw['duration'] / pw['cd']   # (the cloud's share of the time)
# the damage: x1.25 the Pwout on a crowd spread evenly (the fusions' rule, fusions060; the Cawotte hurts no one): the
# cloud at CAL of the Pwout's blow and four Cawottes of (70/120)^2 its area at SATK of the cloud's blow:
# CAL * (1 + 4 * 0.34 * SATK) = 1.25. (The spell bench, sim_node BENCH, is held back by how many monsters come: at CAL 1
# and 0.86 it gave x1.46 / x1.49 the Pwout alone, its maps ranging from 45 to 239 dps for the Pwout itself)
CAL, SATK = 0.8, 0.415
assert abs(CAL * (1 + 4 * (70 / pw['radius']) ** 2 * SATK) - 1.25) < 0.01
C['spells']['fu_pwout_cawotte'] = dict(
    id='fu_pwout_cawotte', t='pwcawotte', sid=0, anim=PW['anim'], animAll=PW['animAll'], animBy=PW['animBy'], fx=[], snd=PW['snd'],
    icon='sf_fu_pwout_cawotte', sfusion=1, cls=None, src=['prouts', 'cawotte'], fkind='global', lv=[],
    name=T('Potagew Pwoutant', 'Fawty Cawwot Patch', 'Pupsendes Kawottenbeet', 'Huewto Pedowwo', 'Owto Petoso', 'Scheetwortewtuin', 'Howta Pumzenta'),
    desc=T("Un Pwout de Cawotte rouge-brun vous suit : il blesse les monstres et vous soigne. Quatre Cawottes surgissent autour de vous et frappent aussi.",
           'A red-brown Cawwot Fawt follows you: it hurts the monsters and heals you. Four Cawwots spring up around you and strike too.',
           'Ein rotbrauner Kawotten-Pups folgt dir: Er verletzt die Monster und heilt dich. Vier Kawotten springen um dich herum hervor und schlagen ebenfalls zu.',
           'Un Pedo de Zanahowia rojizo te sigue: hiere a los monstruos y te cura. Cuatro Zanahowias brotan a tu alrededor y también golpean.',
           'Un Peto di Cawota rosso-bruno ti segue: ferisce i mostri e ti cura. Quattro Cawote spuntano intorno a te e colpiscono anche loro.',
           'Een roodbruine Wortewscheet volgt je: hij verwondt de monsters en geneest jou. Vier Wortews springen rondom je op en slaan ook toe.',
           'Um Pum de Cenouwa castanho-avermelhado segue-te: fere os monstros e cura-te. Quatro Cenouwas brotam à tua volta e também atacam.'),
    base={'dmg': round(pw['dmg'] * CAL, 2), 'radius': pw['radius'], 'tick': pw['tick'], 'duration': pw['duration'], 'cd': pw['cd'],
          'heal': round(cw['heal'] * cw['duration'] / cw['cd'] / up, 3), 'healShop': round(cw['healShop'] * cw['durShop'] / cw['cdShop'] / up, 3),
          'color': '#7a2a14', 'puff': '#8a2c12', 'rim': '#a8401c', 'cawN': 12, 'cloud': 1, 'fart': 1, 'follow': 1,
          'sat': 4, 'satR': 70, 'satK': SATK})
C['spellFusions'].append({'id': 'fu_pwout_cawotte', 'cls': None, 'src': ['prouts', 'cawotte'], 'kind': 'global'})

# weapons banished by type at level-up (ui.js levelUpMenu, Run.banish): the rule said beside Bannir, and in the message
put_ui({'banish_w': T('Bannir une arme exclut tout son type : plus aucune arme de ce type ne sera proposée.',
                      'Banishing a weapon excludes its whole type: no weapon of that type will be offered again.',
                      'Eine Waffe zu verbannen schließt ihre ganze Art aus: Keine Waffe dieser Art wird mehr angeboten.',
                      'Desterrar un arma excluye todo su tipo: ya no se ofrecerá ningún arma de ese tipo.',
                      'Bandire un\'arma esclude tutto il suo tipo: nessuna arma di quel tipo verrà più proposta.',
                      'Een wapen verbannen sluit zijn hele soort uit: geen enkel wapen van die soort wordt nog aangeboden.',
                      'Banir uma arma exclui todo o seu tipo: nenhuma arma desse tipo voltará a ser proposta.'),
        'banished_w': T('{t} : plus aucune arme de ce type ne sera proposée pendant cette partie.', '{t}: no weapon of this type will be offered again this run.',
                        '{t}: Keine Waffe dieser Art wird in diesem Lauf mehr angeboten.', '{t}: ya no se ofrecerá ningún arma de este tipo en esta partida.',
                        '{t}: nessuna arma di questo tipo verrà più proposta in questa partita.', '{t}: geen enkel wapen van deze soort wordt deze run nog aangeboden.',
                        '{t}: nenhuma arma deste tipo voltará a ser proposta nesta partida.')})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('0.95 ok: shields', len(C['shields']), '| removed', len(gone), '| Jorbak', jname['fr'], klepto['fr'], '| Ganymède', C['gany']['name'])
