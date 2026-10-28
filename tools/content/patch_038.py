"""Beta 0.40 content, applied on top of patch_037.   usage: python tools/content/patch_038.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_037 as P7

C, T, G, put_ui = P7.C, P7.T, P7.G, P7.put_ui

# fusions: only those of the characteristics you have are offered, plus 'Brute', the basic one (no characteristic)
if not any(f['id'] == 'brute' for f in C['fusions']):
    C['fusions'].insert(0, dict(id='brute', stat=None, icon='Icon_37', color='#bfb6a4', mul={}, stats={'dmgK': 0.05}, fx='brute',
        name=T('Fusion Brute', 'Raw Fusion', 'Rohe Fusion', 'Fusión Bruta', 'Fusione Bruta', 'Ruwe fusie', 'Fusão Bruta'),
        desc=T('Sans caractéristique : l\'arme se durcit, tous vos dégâts +5 %. La fusion de base, pour les puristes.',
               'No characteristic needed: the weapon hardens, all your damage +5%. The basic fusion, for purists.',
               'Ohne Eigenschaft: Die Waffe härtet sich, all dein Schaden +5 %. Die Grundfusion, für Puristen.',
               'Sin característica: el arma se endurece, todo tu daño +5 %. La fusión básica, para puristas.',
               'Senza caratteristica: l\'arma si indurisce, tutti i tuoi danni +5%. La fusione di base, per puristi.',
               'Zonder eigenschap: het wapen hardt uit, al je schade +5%. De basisfusie, voor puristen.',
               'Sem característica: a arma endurece, todo o teu dano +5%. A fusão básica, para puristas.')))
for f in C['fusions']:
    if f['id'] == 'sagesse':
        f['desc'] = T('Sagesse : quatre étoiles de Sagesse tournent autour de vous et frappent (45 % des dégâts de l\'arme), l\'expérience coule (+20 %).',
                      'Wisdom: four Wisdom stars orbit and strike (45% of the weapon\'s damage), experience flows (+20%).',
                      'Weisheit: Vier Weisheitssterne kreisen und treffen (45 % des Waffenschadens), Erfahrung fließt (+20 %).',
                      'Sabiduría: cuatro estrellas de Sabiduría giran y golpean (45 % del daño del arma), la experiencia fluye (+20 %).',
                      'Saggezza: quattro stelle della Saggezza ruotano e colpiscono (45% dei danni dell\'arma), l\'esperienza scorre (+20%).',
                      'Wijsheid: vier wijsheidssterren draaien rond en raken (45% van de wapenschade), ervaring stroomt (+20%).',
                      'Sabedoria: quatro estrelas da Sabedoria giram e atacam (45% do dano da arma), a experiência flui (+20%).')
    if f.get('stat'):   # (the description says which characteristic opens it)
        f['need'] = f['stat']

# the Coffre Animé and the boss chests: the chest sprite at zoom 6 (it was 2.4 / 3.0: pixelated)
C['monsters']['coffre_anime']['sprite'] = '1083_z60'; C['chestSprite'] = '1083_z60'

# secret: the trapdoor marked 'E' in the Minotoror zone (found on the world picture) -> a blue Coffre Animé, 500 HP, a relic
C['trap'] = dict(map='minotoror', x=824, y=957, r=26, hp=500)
put_ui({
    'trap_found': T('Une trappe ! Un Coffre Animé tout bleu en sort… et lâche les gaz. Battez-le pour sa relique !',
                    'A trapdoor! A bright blue Animated Chest climbs out… and breaks wind. Beat it for its relic!',
                    'Eine Falltür! Eine knallblaue Lebende Truhe klettert heraus… und lässt einen fahren. Besiege sie für ihr Relikt!',
                    '¡Una trampilla! Un Cofre Animado azul sale… y se tira un pedo. ¡Véncelo por su reliquia!',
                    'Una botola! Ne esce un Forziere Animato tutto blu… e molla una puzzetta. Sconfiggilo per la sua reliquia!',
                    'Een valluik! Er klimt een knalblauwe Levende Kist uit… en laat een wind. Versla hem voor zijn relikwie!',
                    'Um alçapão! Sai de lá um Baú Animado todo azul… e solta um pum. Vence-o pela sua relíquia!'),
})

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.40 ok', [f['id'] for f in C['fusions']])
