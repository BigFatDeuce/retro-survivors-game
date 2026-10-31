# Changelog (player-visible changes)

From the Git history and the technical notes. The version shown in
game is **0.98.3** (0.94 was never released on its own: its changes come with 0.95).

## 0.98.3

Balance
- Hard mode: monsters and bosses have +35 % life instead of +37.5 %.
- Objects on the ground no longer have a hidden x1.15: the rates are now the real ones, so Recall Potions, Fairies, Hourglasses,
  powers and the other objects fall 13 % less often than they did.
- Bread drops at a real 0.300 % a monster (x Luck), three times that with Ganymède's blessing. It was 0.259 %.
- **Manuel du Tailleur**: a real rate on every monster, 0.03 %, about one whole run in ten, instead of one roll a run. On a boss it
  goes by the boss's real power: 1 % on the weakest, 5 % on the Goultard.
- TTG cards: 55 % common, 30 % rare, 11.8 % epic, 3.2 % legendary.

What's new
- **Gladiatrool Entry Token**: at 7:30 a token appears anywhere on the map, once a run, shown on the minimap. Its wheel gives a
  characteristic you do not have yet, in a place of its own: it never takes one of your 5. It can be levelled up like the others.
- **Official TTG cards and packs**: the 464 cards and 48 packs are now Ankama's own pictures. A pack holds its theme: a family's
  cards (Gobballs, Blops, Chafers…) or a rarity's. The packs come in a random order and every card can be found.
- The pack opening is new: the pack falls spinning, trembles as stars close in, tears open in a flash with its colours splitting,
  then the card rises and turns over among stars.

Quality of life
- The **Enutrof's thrown shovels** are bigger, with a gold rim and halo, kamas turning round them and a wake of gold.
- The **Trool Fair Token** stands out in the choices: a dark blue rim and sparks.
- The **boss life bars** at the top are redrawn in the XP bar's bronze and gold, the life lost melting away, embers inside. The
  Tofuzmo's green is a little deeper.
- The XP bar ends in a plain round edge instead of a gold cube.
- After a choice or a meeting with ToT, the game comes back from a near stop to full speed over half a second: your keys are yours
  again before the monsters move.
- In the shop's spells, a spell that fuses with a weapon shows that weapon's icon beside the fusion's, which now stands in the middle.
- Hats, Cloaks, Shields and Pets get an **Owned** filter beside the search, each tab its own; the two work together.
- The Rogue's **Bomberfus** are 1.5 times bigger.
- The keyboard and controller cursor goes away as soon as the mouse is used, and comes back with them. It no longer stays over a
  window on the button behind it.
- The frames of the messages (events, bosses, relics, a Dofus found) are in Dofus Retro's brown instead of green, without their
  leaves, with lights running along their edge and tiny sparks like the menus' cursor; a relic's frame throws sparks out of both
  sides, and its word « Relic » is a plain word in the chat's lettering.
- The Sablier's timer is ice blue and high on the screen, little hourglasses turning round it among hanging crystals.
- A spell fusion's name is back in violet, in capitals in the chat's lettering, its letters splitting into red and cyan, sparks
  all round it.
- The leaves of the countdown, GO! and the victory are softer and no longer jump out of the picture.
- **Phones**: the in-game interface is much bigger, upright and lying down: spells, heart, chat, map, the touch joystick.
  Upright, the spells sit under the timer and the chat over the heart, across the screen. Ganymède's and Dark Vlad's scenes
  have bigger lines; lying down, the picture sits beside the text.
- In the chat, the beginners' help and Ganymède's blessing share one message on the first three maps; after that the blessing has
  its own.

Fixes
- The relics' tip said six per run: five can fall.
- The blue light round the message frames passes behind their gold diamonds.
- The last line of the end screen (« Your ghost… », « You beat the final boss… ») has the colour of the line beside the grade.
- In dark mode, the monsters' names are white in the TTG binder and when a pack opens.
- The manuals give the real odds: Luck where it counts, the new rates, the real rarity of the TTG cards.
- Phones: the music and sounds stop at once when the screen is locked or the game goes to the background (the Android app kept
  playing).

## 0.98.2

Balance
- Every spell, global spell and spell fusion deals 10 % more damage (weapons and summoned allies from drops are unchanged).
- The experience needed for levels 2 to 5 is 10 % lower, in every mode; from level 5 on nothing changes.
- **2 Banishes** per run instead of 1, shared by spells, weapons and characteristics.
- The **Arakne Agressive** and the **Arakne Majeure** from drops no longer push what they hit: they slow it by 90 % for 2 s
  (not bosses, as with the push).
- **Ganymède's blessing**: on the first 10 maps in Normal, +5 % damage and 3 times more bread on the ground (a gift from the
  Incarnam baker), on top of the help on maps 1 to 3.

What's new
- On map 11 in Normal, Dark Vlad comes to take these blessings away.

Quality of life
- Every message in the middle of the screen is in the victory's gold (a critical hit's word stays red).
- The Sablier shows a see-through timer in the middle of the screen while the monsters are frozen.
- The countdown's chromatic aberration starts with the countdown and grows over its first second.
- A run's sounds and pictures are all ready before the countdown, which waits if they are not.
- The messages in the middle of the screen give a name only (Eclipse, Kama rain, Tofuzmo, a boss's name…); what it does
  stays in the chat at the bottom left, twice as long as before. A critical summon shows « Critical hit! » in red before
  its name. These names and the relics' names use the chat's lettering.
- A spell fusion's name is written in capitals, in gold like the victory (was violet).
- **Lethal Attack** (Sram) and its fusion hit their monster at once: no mark on the ground, no delay to step out of.
- Smoother: the first level-up no longer freezes the game for a moment (its pictures are prepared during the countdown),
  and while a choice or the pause is open the game no longer redraws the frozen fight behind it (less work, less battery
  on phones).

## 0.98.1

Balance
- Every spell, global spell and spell fusion recharges 15 % slower; the Cra's spells and fusions 20 % slower (Flèche
  Enflammée 15 %). Weapons are unchanged.
- Hard mode: every monster and boss has 10 % more life.
- An elite drops a relic 15 % of the time (was 25 %).
- **Dofus Ocre** -5 % cooldowns (was -10 %), **Dofus Cawotte** +15 % experience (was +25 %), **Dofus Pourpre** +15 %
  damage (was +25 %).
- The **Arakne Majeure** (an Arakne's critical summon) doubles your damage while it stays.

Quality of life
- A choice that pops up during a run accepts Space / E after 0.3 s (was 2 s).
- A critical Arakne or Chaferfu summon (Arakne Majeure, Chaferfu Lancer): the game nearly stops for 2 seconds under
  confetti and a strong chromatic aberration, the camera closes in on it, then comes back.
- The Aggressive Arachnee, the Arakne Majeure and the Chaferfu Lancer are drawn sharper (re-rendered from the client's
  vector art at their size on screen); the Aggressive Arachnee now has its attack animation.
- Spell fusions in the run's spell bar have a violet edge with lights running round it and twinkling stars.
- The chromatic aberration of the countdown runs from the « 2 » to half a second after GO!.
- The Hard mode's texts and the manuals give its real life bonus (+37.5 %); the manuals list the Manuel du Tailleur's
  chance on every boss.
- Tiny sparks around the menus' cursor (controller and keyboard).

## 0.98

Balance
- **Invisibilité** (Sram): at 5/5 in the shop, 25 s between two (was 15.2 s) and 1.5 s invisible (was 2.3 s).
- **Flèche Explosive** (Cra): 20 damage at 5/5 (was 23.6), 2 s between two (was 1.5 s). **Flèche Magique** no longer
  pushes monsters back (nor the arrows of its fusion, Flèche Punitive).
- **Attaque Mortelle** (Sram): one blow on one monster only (no area, no extra copies), the strongest one right next to
  you (about 2 m), twice the damage on bosses. Its fusion with Toile d'Arakne, **Piège Mortel**: the same with twice the
  reach, and an Arakne web under the monster hit.
- 25 % less damage: **Frappe du Craqueleur** (Osamodas), **Fiole Corrosive** (Otomaï, its puddle too), **Dagues
  Boomerang** (Roublard), **Lancer de Pièces** (Enutrof), **Marteau de Moon**, **Toile d'Arakne**. **Épée du Jugement**
  (Iop): 35 % less damage.
- **Intelligence**: at 5/5 in the shop, its four levels give +42.5 % area (was +50 %).
- **Manuel du Tailleur**: every boss may now drop it, from 1 % (Bouftou Royal) to 5 % (Goultard), more the further the
  boss is in the game.
- **Invisibilité** (Sram): monsters' blows and projectiles still miss you, but their areas on the ground (puddles,
  marked circles, charges, breaths) now hit you.
- **Piège Sournois** and **Piège Empoisonné** (Sram): half as wide, twice the time between two, 50 % more damage, one
  trap a cast. The Piège Sournois: one on the ground at a time (the new one replaces it), it goes off when a monster
  touches its drawn area. The Piège Empoisonné: several can wait on the ground; it goes off when a monster steps on its
  cone in the middle, hits its whole area and leaves a gas cloud for one second that poisons every monster passing
  through it, once.
- **Bénédiction Animale** (Osamodas): the Boufcouls no longer hit around them on every blow; each one bursts once when
  it dies or goes, around it (five of its blows). Each one hits at its own pace.
- **Rempart élémentaire** (Féca): three times the damage, a quarter smaller, twice the time between two.
- **Explobombe** (Roublard): a little more time between two (+15 %), its fuse a quarter shorter.
- Poisoned spells (Poison insidieux, Flèche Empoisonnée, Flèche Harcelante, and the poison of Poison Paralysant and
  Mutagen) leave a small poison cloud where they hit, for a quarter of a second: the monsters around are poisoned too.
- Bosses have 15 % less life.
- The damage bonus of your level now reaches its top (+9.9 %) at level 50 instead of level 100.
- Levels 1 to 5 need 20 % less experience; the difference comes back little by little between levels 20 and 50.
- Cooldowns grow slowly with your level: at level 50, +20 % for the fastest spells down to +10 % for the slowest.

Quality of life
- After 11:00, a boss's fall slows the game four times less long; a fusion made by a boss chest no longer slows it.
- The Manuel du Tailleur's slot machine: press the action button twice (A, Enter…) or tap the reel twice to see the prize at once.
- The Ambre Ancestrale is half as big on the ground, with a soft glow.
- Every area that stays on the ground (spell zones, traps, the monsters' puddles) melts into the ground: no outline, its
  edge fading out, its lines quieter, sparks of its element rising around it. The Boule de Chaos, Vent Empoisonné,
  domes and webs are softened the same way.
- **New lettering for the announcements**, closer to Dofus Unity's: the countdown, GO!, the messages in the middle of
  the screen, the victory and the end-of-run summary. The countdown's emblem is now green and alive (a wreath of leaves,
  a glowing Dofus egg, fireflies), GO! and the victory throw leaves, the messages sit in a green frame with a gold edge;
  the relics' captions use it too. After a victory, rays and leaves fill the whole summary window.
- A chromatic aberration, like a camera lens (the screen's edges softly blurred, small colour fringes): during the
  countdown, strongly right after GO!, in the slow motions, when a boss falls, when a relic is picked up, when
  Libération saves you (with a short slow motion) and very strongly at the victory. GO!'s swords are now two Épées
  Royales du Bouftou, without the two light blades at its sides.
- A boss's arrival: a bigger, light green frame that glows, with sparks. A relic's caption: a see-through green frame
  with green flames, its bonus written in a rounder, easier font. The messages in the middle of the screen (monsters,
  bosses, events) use that rounder font too; titles and names keep the announcements' lettering.
- The Ambre Ancestrale a quarter bigger than before on the ground, the Ambre du Chêne Mou half as big.
- The controller's cursor glides from one button to the next, with a light running round it.
- The run's messages at the bottom left sit on a soft shade (they read on bright grass); the menus' values no longer
  break in the middle (a unit alone on the next line).
- The dash, moving-spell, auto-pick, pause and full-screen buttons in the green and gold style, alive when ready; the
  "2×" hint under the dash is bigger on phones and tablets.
- Spells, weapons and characteristics use one colour code in the menus (level-up cards, shop, Armoury, chests), as in
  Dofus 2's tooltips: the description in orange, what it does in green (damage, heals, bonuses), its other numbers
  (cooldown, area, duration…) with the value in bold, a condition in red, a special effect in blue.
- The installed games look for a new version at every launch (a new version could stay unseen for 6 hours).

## 0.97

New zone
- **Île de Frigost** (zone 17, right after L'île de Grobe, opens when Grobe is won — already open if you won Grobe
  before): a snowy island at Grobe's difficulty, a little over it. A village with its keep, ice towers and crystal lamps,
  a frozen lake, the lost pines' wood and a crevasse of ice blocks. Its monsters are Frigost's from the Dofus Retro
  files: the Boufmouths (Bouftonmouth, Boufmouth, Boufmouth de guerre), the Bulbeneige, the Épouvantail de Frostiz,
  the Tremble Ensorcelé, the Craqueboule d'Obsidienne, the Dévoreur de Poisskaille, with the Kanigrou hivernal and the
  Sakai Firefoux; its bosses the Boufmouth légendaire, the Abominable Yiti and Royalmouth. Its own music, its own
  boss music, a treasure for Musha's maps.

Treasures
- **The Chouque's ghost** has a new story: a pirate captain thrown overboard by a certain Kack Sparo, who hid his
  treasures all over the World of Twelve. New lines, his own music while he talks, and his hints are easier to read.
- A dug treasure now also holds, one time in two, a **shield** or a **Dofus** you don't have yet.
- More profile names hide a little secret.

Gameplay
- **Bague Houx**, a new rare object on the ground (three times rarer than a spell scroll like Flamiche): picked up, it
  gives one more reroll for your level-up choices, on top of the ones you have.

Look and feel
- The dialogue bubbles of ToT, Ganymède, Musha and Dark Vlad use the rounded font of the tips, and ToT's bubble has
  its margins back (its text touched the edges).
- Heals that land together show one green number that adds up (the Cawotte's heals wrote two numbers on top of each
  other).
- A hat put on in the shop or bought from the travelling merchant gives the Iop his short hair at once (his long hair
  stayed until the next run).

Texts
- Tips brought up to date: the Dofus drop from a few bosses each, elites can drop relics, the treasure maps come from
  Jorbak, a fusion only needs your weapon at its top level. The loading screen's first tips are current ones, in every
  language.
- Translations added where they were missing (a few hats, pets, shields, Archimonsters and a TTG card in German,
  Italian, Dutch or Portuguese; the Frigost monsters in Dutch and Portuguese).

Android
- Closing the app stops the music and the sounds at once (they went on for a few seconds).

Options
- Typing in the save code box (or any text field) no longer triggers the keyboard shortcuts: E, P, A no longer press a
  button or close the window; Échap closes it.
- **Camera**: the far and close settings zoom 20 % out / in (they did 10 %).

Controls
- **Phone / tablet**: the double tap dashes the way the joystick points, as a controller's stick does (it went towards
  the tapped spot); with no joystick held, the way you last walked.
- **F1** (keyboard) and **R3** (the right stick's click, controller) switch between the light and dark menus.

Gameplay
- **Potagew Pwoutant** (Pwout de Cawotte + Cawotte fusion): its four Cawottes now stay planted where they spring up,
  like traps, instead of following you. It comes back half as often (10.5 s), and each of its blows and heals is twice
  as strong (same damage and healing over a minute). Its cloud also heals your summons that monsters can hurt.

Armoury
- **Fusions tab**: the fusions that heal show it — life steal (Mot Drainant, Transfert de Vie: a share of the damage
  dealt) and heal over time (Potagew Pwoutant: HP a second in its cloud).

## 0.96

New
- **Boule de Chaos**, a new global spell: a big violet fireball that rushes straight at the nearest monster and explodes
  on the first one it touches, hurting everything around.
- **Marteau du Chaos**, a new spell fusion for every class (Boule de Chaos + Marteau de Moon): the Marteau de Moon's
  hammers hit 30 % harder, glow violet and open little rifts of the Void where they strike (0.5 s, light damage).
- **Armoury, Fusions tab**: each fusion shows its damage and cooldown (with your shop levels).

Gameplay
- **Élagage de cou** (Brigandin): 1.5 s cooldown, 1 s with the whole shop (it was shorter).
- **Cupidité** (Enutrof): attacks 10 % more often.
- **Roublard**: 110 % move speed (107 % before). **Écaflip**: 115 % strength, 110 % speed (105 % each before).
- **Immunité** (Féca): 35 s cooldown and 1.5 s of immunity at its first level, 30 s and 2 s with the whole shop; its
  levels still improve it.
- **Cupidité** (Enutrof fusion) is now a little stronger than Lancer de Pièces at its top level (it was weaker), and
  **Élagage de tête** (Brigandin fusion) about 20 % stronger than Élagage de cou at its top level (it was far above).
- **Iop**: 115 % strength on the class card, and his +12 % damage is now really applied on top (127 % in a run).
- **Démultiplication** and the **Craqueleur's legendary belt**: the extra projectiles, summons, orbs, strikes, bombs and
  beams they add deal 50 % damage (as many things on screen, but no more double or triple damage on spells with one or two
  copies).
- The shop's upgrades of a spell (duration, summons' life, shields) now apply from its first level, not from its second.
- A character no longer picks anything up while falling: a chest under the body opened its window after death.

Fixes (texts that said something else than the game does)
- Écaflip's passive: +15 % luck (it said critical hits). Osamodas's: +40 % summon damage (it said 20 %).
- La bonne Pioche no longer claims "every 5 seconds"; the Pieu vampirique goes through 3 more monsters (it said 4).
- The Tofuzmo's announcement shows its real life (it said 1000 with 700); the crows' warning gives their real time
  (it said 10:00 when they come at 11:00); the Hard mode's tooltip on the play screen gives the current numbers; the ToT
  tip mentions Jorbak.
- The level-up cards and the Armoury show the bombs' and the Cawottes' real area and duration (Intelligence, Durée).

Look and feel
- **The Chouque's ghost** keeps each line on screen twice as long again.
- **Reroll**: once the new cards have turned over, they no longer give a little extra flip at the end.
- **Épée du Destin** (Iop): the line of fire that flashed on every monster touched is gone; the swords' hits stay
  readable.
- The shop's cards show the real cooldown and duration of the spells that have their own shop values (Cawotte,
  Immunité, Élagage de cou).

## 0.95

New
- **Ganymède, the guide**: a short scene with him a few seconds into each of the first three zones (once, the game
  paused), and another one when Hard mode is unlocked.
- **Help for beginners**: on the first three zones in Normal, until you win there in Normal, monsters have less life
  (−30 / −20 / −10 %) and hit half as hard. A message in the chat says so.
- **Hard mode is unlocked by winning L'île de Grobe** (players who already won it keep it).
- **Jorbak** replaces the Tofuzmo from the zone after the 10th: 3 000 HP, keeps 10–15 m away from you and pushes you
  back with his *Kleptomanie psychopathe* if you get within 1 m. Beating him gives a +15 % bonus.
- **Options**: Visual effects (Full / Reduced / Minimal) for less powerful PCs and phones, and the Camera distance
  (Far / Normal / Close, smooth). The 'Renderer' row is gone (PixiJS always; the old renderer only steps in by itself
  if the graphics card fails).

Gameplay
- **Treasure maps** now drop only from Jorbak (1 chance in 2 at each kill, while maps are left to find); the Maîtres
  Corbacs give the Manuel.
- **Tofuzmo**: 1 000 HP.
- **Monster heals**: a monster is healed once per run at most (bosses' own heals, healer monsters such as
  the Gelées and Blops).
- **Démultiplication** shows up half as often at level-up.
- **Arakne majeure** (Arakne Agressive): pushes only once, three times as far.
- **Weapons** show up about 25 % more often in the level-up choices.
- **Banish**: banishing a weapon now removes its whole type (all the swords, all the staffs…) from the choices for the
  rest of the run; the level-up window says so.
- **Brigandin**: +10 % kamas instead of +30 %.
- **Enutrof**: moves 5 % faster.
- **Lancer de Pièces**: the coins fly in a tighter spray; the spell recharges 30 % faster, and faster again at each level
  (up to +50 % at its top level).
- **New spell fusion, Potagew Pwoutant** (Pwout de Cawotte + Cawotte, any class): a red-brown Pwout follows you, hurts
  the monsters and heals you, and four Cawottes spring up around you and hit too.
- **The Chouque's ghost** (treasure maps): each of his lines stays twice as long.
- **Shields**: the Primordial shields (except the Bricoleur's) and the Polykrome shields are gone — bought ones are
  refunded; the shields are sorted by price.

Look and feel
- **Endless**: the final bosses that come back from 10:00 drop the Tailor's Manual less often — 5 % at 10:00, then 2.5 % more
  every minute (7.5 % at 11:00, 10 % at 12:00…) instead of 50 %.
- **Reroll**: the new cards turn over slower and cleanly (the flip was too fast and could twist).
- **Update notice** (Windows, Linux, Android): when a newer version is out, the main menu says so and its button opens
  the download page.
- **Controller cursor** in the menus: bright turquoise with a dark edge, easy to see on every button.
- Monster shadows smaller and lighter; the reroll dice no longer overlap (a single die, preloaded).
- **Reroll**: the cards gather into a deck under the die, then are dealt face down (a casino card back with Ecaflip's
  clover) and turn over once, with a golden sheen.
- The countdown's numbers and GO! centred; the event messages centred in their frame; a relic shows 'Relic!', its name
  and its bonus on three lines in a lighter, smaller frame **above** the relic, which springs out of your character and
  floats over its head — the character stays visible; it stays 3 s instead of 3.8.
- **XP bar** redrawn in the countdown's style (bronze and gold frame, amber fill, the level on a small plate; same font);
  the **windows' frames** to match — the windows over the game get a wider gold frame with diamonds on the corners, a
  gold rule under their title and a light sheen —, and new **close buttons** (gold-ringed, they warm up and turn when
  hovered).
- **Bestiary**: the Tofuzmo and Jorbak listed in the zones where they come.
- Smoother with big crowds of monsters (about 10 % less work per frame on a slow processor, more with Reduced or Minimal effects),
  and with the spells and weapons that were the heaviest (marking spells, life-stealing weapons, damage zones, melee
  blows, damage numbers); about 30 % less graphics memory once the menu has preloaded the effects.

- **Announcements redone** in a new font, Cinzel (carved gold capitals in the spirit of the logo): countdown, GO!,
  Victory, You died…, fusion names, banners, relic and Dofus captions, the end screen's title.
- Countdown: a riveted gold medallion with blades, turning runes, a burning time arc and the Dofus spiral; each number
  is struck in like a seal and heats up from gold to ember red. GO!: the medallion bursts, the swords clash, burning
  leaves fly out and GO! drops in white-hot forged gold with blades of light and a fire aura, then burns away to embers.
- Victory: a blade of light opens, the letters strike in from the centre, gold rules and a sheen; You died…: a crimson
  cut, the letters sink in one by one, blood drips and ash falls.

## 0.90 – 0.94

New
- **New class: the Otomaï** (0.91), the alchemist: Fiole Corrosive, Brume Mutagène, Élixir de Mutation, Appel des Kidos,
  Transmutation (weakened monsters turn to gold), Potion de Soin, and 3 fusions.
- **Shields** (0.92): the official game's 276 shields in the shop (new tab, search, preview), +1 resistance (not for the
  Roublard, the Brigandin or the Otomaï).
- **5 new achievements** (0.92): a singing name, Nowel's gifts, zones won in Hard mode, the Maîtres Corbacs' rewards,
  the "fah".
- **Discord button** in the main menu (0.92); thanks after the first victory over Goultard (0.91).
- **Small secrets** (0.92): some profile names play a sound, victory confetti, a mark on zones won in Hard mode.
- **Armurerie: Relics tab** (0.94): every relic of the game, the ones found highlighted.
- **Android version (APK)** (0.94).

Gameplay
- Maîtres Corbacs: a treasure map or a Manuel every minute from 11:00 (0.92).
- Crâ: arrows push 25 % less (0.92); **one projectile less at the top of every spell** (0.94).
- Smaller ancestral amber (0.92); dropped items no longer overlap and stay in the field (0.92).
- Enemy projectiles blink before they vanish (0.92).
- Sram traps and Piège Empoisonné redrawn; Toile d'Arakne animated with tiny Araknes (0.92).
- **Hard mode: 1.5× more kamas on the ground** and a message listing the differences at the start of a run (0.94).
- **Shop: Vitality** from +10 % (0/5) to +20 % (5/5) max HP per level, **Action points** from -3 % to -5 % cooldown
  per level (0.94).
- **Tofuzmo**: the reach of its contact blows a third shorter (0.94); its size, life and bonus (+10 %) unchanged.
- **Nowel**: a chat reminder (at the start, then every 2 min 30) that the zone gives no kamas, only gifts (0.94).

Graphics and interface
- Characters behind trees and scenery, see-through when hidden (0.91); colours true to the client, no shimmer (0.91);
  capes flapping while running, accessories in the character's colours (0.91).
- Hair and hats as in the official game (0.91–0.92); capes and hats in the right order for each direction (0.92); the
  shield no longer shows its face on the back while running (except the male Sadida) (0.94).
- Fusion name reveal redone (0.92); "GO!" countdown with swords (0.91); sharper icons when shown big (0.91).
- Controller: colour palette, shop preview, search, default selection (0.92).
- Language flags visible on phones (0.92); mini maps without a dark line (0.92).
- **Phones** (0.94): no more overlaps in the menus, upright or sideways (play screen, shop, bestiary, controls,
  options, end screen); the chat no longer passes under the heart.

Performance and stability
- **Crash after about ten character changes fixed** (0.93): memory no longer grows.
- Images decoded off the main thread: runs load about 2× faster, fewer stutters (0.93).
- Default resolution: 1080p on the web, native in the desktop app (0.93); the GPU in use is shown in the options (0.93).

Saves and compatibility
- A damaged or hand-edited save no longer blocks the boot (0.94); missing settings get their default value (0.94).
- Keyboard / controller: a volume slider of a closed screen no longer changes by itself; the highlight comes back at
  once after Escape / B (0.94).
- The game's sounds and pictures carry no metadata (0.94).

Not tested on a real phone: the 0.94 changes.
