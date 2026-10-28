"""Beta 0.33 content, applied on top of patch_031: the skin merchant (game/js/extras.js spawnMerchant): he comes once
per run after 5 minutes, at a random spot shown on the minimap, with 5 random hats / capes / pets at -25 to -75 %;
what is bought is kept (shop collection). He is no longer one of the random events.
->  game/data/content.json      usage: python tools/content/patch_032.py"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
import _root
import json
import patch_031 as P1

C, T, G = P1.C, P1.T, P1.G
C['merchant'] = dict(t=300, stay=120)
C['randEvents']['list'] = [k for k in C['randEvents']['list'] if k != 'merchant']
UI = {
    'ev_merchant': T('Un marchand ambulant s\'est installé quelque part ! (voir la mini-carte)', 'A travelling merchant has set up shop somewhere! (see the minimap)', 'Ein fahrender Händler hat irgendwo seinen Stand! (siehe Minikarte)', '¡Un mercader ambulante se ha instalado en algún lugar! (mira el minimapa)', 'Un mercante ambulante si è sistemato da qualche parte! (vedi la minimappa)', 'Een rondreizende handelaar staat ergens! (zie de minikaart)', 'Um mercador ambulante instalou-se algures! (vê o minimapa)'),
    'merchant_hello': T('« Des coiffes, des capes, des familiers… Tout est soldé, rien n\'est repris ! »', '"Hats, capes, pets… Everything\'s on sale, no refunds!"', '„Hüte, Umhänge, Begleiter… Alles reduziert, kein Umtausch!"', '«¡Sombreros, capas, mascotas… Todo rebajado, sin devoluciones!»', '«Cappelli, mantelli, famigli… Tutto scontato, niente rimborsi!»', '"Hoeden, capes, huisdieren… Alles in de uitverkoop, niet retour!"', '«Chapéus, capas, mascotes… Tudo em saldo, sem devoluções!»'),
    'm_kept': T('Vendu ! Il est à vous, même après la partie.', 'Sold! It\'s yours, even after the run.', 'Verkauft! Gehört dir, auch nach dem Lauf.', '¡Vendido! Es tuyo, incluso después de la partida.', 'Venduto! È tuo, anche dopo la partita.', 'Verkocht! Hij is van jou, ook na de run.', 'Vendido! É teu, mesmo depois da partida.'),
}
for k, v in UI.items():
    for lg, txt in v.items(): C['ui'][lg][k] = txt

if __name__ == '__main__':
    json.dump(C, open(f'{G}/data/content.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('0.33 ok', C['randEvents']['list'])
