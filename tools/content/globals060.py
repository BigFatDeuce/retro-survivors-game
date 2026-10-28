"""0.60: three new global spells (offered to every class), from the Dofus world:
  tofus_kamikazes        summons: overexcited Tofus rush the monsters and blow up on contact
  toile_arakne           zone: an Arakne web on the thickest crowd, it slows and nibbles whatever is caught in it
  eboulement_craqueleur  strikes: Crackler rocks fall on random monsters and stun them
Icons: tools/assets/build_globalicons060.py (sp_g_tofus / sp_g_toile / sp_g_eboul). apply(C) is called by patch_060."""

LG = ('fr', 'en', 'de', 'es', 'it', 'nl', 'pt')
def T7(*a): return dict(zip(LG, a))


SPELLS = {
    'tofus_kamikazes': dict(t='summon', icon='g_tofus', fx=[1100], snd='Poolay_Die', glob=1, anim=None, sid=0,
        base={'dmg': 30, 'count': 2, 'hp': 1, 'speed': 270, 'duration': 6.0, 'cd': 4.6, 'radius': 58, 'kamikaze': 1, 'spriteKey': None},
        lv=[{}, {'dmg': 36}, {'count': 3}, {'radius': 68, 'dmg': 42}, {'count': 4}, {'dmg': 54, 'radius': 76}],
        name=T7('Tofus Kamikazes', 'Kamikaze Tofus', 'Kamikaze-Tofus', 'Tofus Kamikazes', 'Tofu Kamikaze', 'Kamikaze-Tofu\'s', 'Tofus Kamikazes'),
        desc=T7("Des Tofus surexcités foncent sur les monstres et explosent au contact. Ils n'ont jamais été très malins, mais ils sont très motivés.",
                "Overexcited Tofus rush the monsters and blow up on contact. Never very bright, but very motivated.",
                "Überdrehte Tofus stürmen auf die Monster zu und explodieren bei Kontakt. Nie besonders klug, aber sehr motiviert.",
                "Tofus sobreexcitados se lanzan contra los monstruos y explotan al contacto. Nunca muy listos, pero muy motivados.",
                "Tofu sovraeccitati si lanciano sui mostri ed esplodono al contatto. Mai molto furbi, ma molto motivati.",
                "Overenthousiaste Tofu's stormen op de monsters af en ontploffen bij contact. Nooit erg slim, wel erg gemotiveerd.",
                "Tofus superanimados avançam contra os monstros e explodem ao contato. Nunca foram espertos, mas são muito motivados.")),
    'toile_arakne': dict(t='zone', icon='g_toile', fx=[], snd='Brouture_Die', glob=1, anim=None, sid=0,
        base={'dmg': 5.5, 'radius': 82, 'duration': 4.0, 'tick': 0.5, 'cd': 5.6, 'count': 1, 'color': '#e4e4f0', 'slow': 0.55, 'target': 'cluster', 'web': 1},
        lv=[{}, {'dmg': 7.5}, {'radius': 96}, {'count': 2}, {'slow': 0.65, 'dmg': 9.5}, {'duration': 5.5, 'dmg': 12}],
        name=T7("Toile d'Arakne", 'Arachnee Web', 'Arakne-Netz', 'Tela de Arakna', 'Ragnatela di Arakne', 'Arakne-web', 'Teia de Arakne'),
        desc=T7("Une toile d'Arakne tombe sur le plus gros groupe de monstres : ils s'engluent, ralentissent et se font grignoter. L'Arakne, elle, n'a rien demandé.",
                "An Arachnee web drops on the biggest group of monsters: they get stuck, slow down and get nibbled. The Arachnee didn't ask for any of this.",
                "Ein Arakne-Netz fällt auf die größte Monstergruppe: sie kleben fest, werden langsamer und angeknabbert. Die Arakne hat nicht darum gebeten.",
                "Una tela de Arakna cae sobre el grupo de monstruos más grande: se quedan pegados, se ralentizan y los mordisquean. La Arakna no pidió nada.",
                "Una ragnatela di Arakne cade sul gruppo di mostri più grande: restano invischiati, rallentano e vengono rosicchiati. L'Arakne non ha chiesto niente.",
                "Een Arakne-web valt op de grootste groep monsters: ze blijven plakken, vertragen en worden aangeknaagd. De Arakne vroeg nergens om.",
                "Uma teia de Arakne cai sobre o maior grupo de monstros: eles grudam, ficam lentos e são mordiscados. A Arakne não pediu nada.")),
    'eboulement_craqueleur': dict(t='strike', icon='g_eboul', fx=[1003], snd='impact_lourd', glob=1, anim=None, sid=0,
        base={'dmg': 34, 'count': 3, 'radius': 48, 'delay': 0.75, 'cd': 4.3, 'stun': 0.8, 'shake': 3, 'target': 'random', 'rock': 1, 'color': '#c8b89a'},
        lv=[{}, {'dmg': 42}, {'count': 4}, {'radius': 56}, {'dmg': 52, 'stun': 1.0}, {'count': 6, 'dmg': 64}],
        name=T7('Éboulement du Craqueleur', 'Crackler Rockfall', 'Krachler-Steinschlag', 'Desprendimiento del Crujidor', 'Frana del Croccaroc', 'Krakler-lawine', 'Desmoronamento do Crackler'),
        desc=T7("Des rochers de Craqueleur tombent du ciel sur des monstres au hasard et les étourdissent. Le Craqueleur cherche encore ses cailloux.",
                "Crackler rocks fall from the sky on random monsters and stun them. The Crackler is still looking for his pebbles.",
                "Krachler-Felsen fallen vom Himmel auf zufällige Monster und betäuben sie. Der Krachler sucht immer noch seine Kiesel.",
                "Rocas de Crujidor caen del cielo sobre monstruos al azar y los aturden. El Crujidor sigue buscando sus piedras.",
                "Rocce di Croccaroc cadono dal cielo su mostri a caso e li stordiscono. Il Croccaroc cerca ancora i suoi sassolini.",
                "Krakler-rotsen vallen uit de lucht op willekeurige monsters en verdoven ze. De Krakler zoekt zijn kiezels nog.",
                "Rochas de Crackler caem do céu sobre monstros ao acaso e os atordoam. O Crackler ainda procura suas pedrinhas.")),
}


def apply(C):
    for sid, d in SPELLS.items():
        sp = {k: v for k, v in d.items()}; sp['id'] = sid
        if sid == 'tofus_kamikazes': sp['base'] = dict(sp['base'], spriteKey=C['monsters']['tofu']['sprite'])
        C['spells'][sid] = sp
        if not any(g['id'] == sid for g in C['globalSpells']): C['globalSpells'].insert(len(C['globalSpells']) - 1, {'id': sid, 'w': 1.0})
