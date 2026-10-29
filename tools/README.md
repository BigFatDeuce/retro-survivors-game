# tools/ — what each tool is for

Python 3 (Pillow, numpy, OpenCV, Playwright) and Node scripts that build the game's content and pictures from the Dofus
Retro client, test the game and package it. The game itself (`game/`) needs none of them to run.

Every tool works from any folder: paths start from the repository root (`tools/_root.py`; override with `RS_ROOT`).
Run them as `python tools/<folder>/<tool>.py …` (on Windows add `-X utf8` or `PYTHONUTF8=1` for the content chain;
`make_content.py` does it by itself). Each tool's docstring is its manual: read it before running the tool.

**Pick the tool for a task**

| task | command |
|---|---|
| play the current files in a browser | `play_local.bat` / `./play_local.sh` (→ `tools/serve_local.py`) |
| change game data (stats, texts, spells, zones…) | edit the newest `tools/content/patch_*.py`, then `python tools/make_content.py` |
| check the content chain still rebuilds content.json | `python tools/make_content.py --check` |
| test after changing `game/js` | `python tools/qa.py quick` (~5 min) — or at least `python tools/check.py` (~3 min) |
| full test before a release | `python tools/qa.py full --web` (~1 h 30) |
| bump the version | `python tools/bump_build.py 0.95` |
| build Windows / Linux / Android / web | `make_exe.*`, `make_appimage.*`, `make_apk.*`, `python tools/make_dist.py` |
| publish the web version | `publish_cloudflare.bat` / `.sh` (asks nothing: it publishes) |
| publish the source to GitHub (this repository, then the public one) | `publish_github.bat` / `.sh` (asks before each step); `publish_github_fresh.bat` / `.sh` restarts the public repository from one commit |
| re-render a picture from the client | find its builder below (`tools/assets/`) |

## Layout

| folder | holds | rule |
|---|---|---|
| `tools/*.py` | the commands people run (build, test, publish, content) | short, stable names |
| `tools/content/` | the content chain: `patch_v20.py` → … → the newest `patch_<version>.py`, and the data modules they import | only the content pipeline |
| `tools/assets/` | builders that render `game/assets/` + `game/data/sprites.json` from the client | one builder per kind of picture |
| `tools/lib/` | modules shared by many tools (SWF reading, FFDec rendering, maps, sprites.json writes, build helpers) | imported, rarely run |
| `tools/research/` | measurements against the real client (accessory alignment, map finding, colours) and the fixes they produced | run when a question about the client comes back |
| `tools/checks/` | the test suites `qa.py` and `check.py` run, the simulator, the stress tool | |
| `tools/win/`, `tools/android/` | the desktop shell (Electron `main.js`, icons, `find_python.bat`) and the Android WebView app | used by the builds |

How imports work: `_root.py` puts every folder above on `sys.path`, so any tool imports any other by its bare name
(`import swflib`, `import build_icons20 as B`). A tool in a sub-folder starts with
`_sys.path.insert(0, <tools/>)` then `from _root import ROOT` — copy that header from any tool. Module names are unique
across the folders: keep them so.

Names: the number in a name (`build_mobs20`, `build_acc060`, `patch_091`) is the version the tool appeared in (20 = v2.0,
060 = 0.60), not a version of the tool. Tools with different numbers and similar names do different jobs (the three
`build_staticons*` render three different sets of icons); retired ones are listed at the end.

Shared rules for builders:
- write `game/data/sprites.json` only through `sprio.update(fn)` (lock + atomic replace); run sheet builders one at a
  time (two builders writing sprites.json in parallel lost entries in 0.70);
- read the 1.41.9 client from `_root.RAW` (`raw/rc/`) and the up-to-date installed client from `_root.CLIENT`
  (`%LOCALAPPDATA%/Ankama/Retro/resources/app/retroclient`, override with `RS_NEWCLIENT`);
- render vector art at the size it is shown; never upscale map decor (dropped in 0.52); media files carry
  no metadata (`python tools/strip_meta.py` after adding sounds or music);
- scratch output goes to `work/<tool>/` (ignored by Git, rebuilt on demand).

## Commands — `tools/*.py`

| tool | what it does |
|---|---|
| `make_content.py [--check]` | runs the newest `content/patch_*.py`: rebuilds `game/data/content.json`; `--check` only compares |
| `check.py [--bench…]` | the safety net (0.59): simulations of every class + 4 bot runs in Chromium (PixiJS and Canvas 2D), no page error, no missing file; exit code 0 = pass |
| `qa.py quick\|full [--web] [--only a,b] [--list]` | every automated test in order, report in `work/qa/<date>-<suite>/report.md` (see `docs/TESTING.md`) |
| `serve_local.py [port] [--no-browser]` | local web server for `game/` (first free port from 8765, no cache), opens the browser |
| `make_dist.py [baseline_dir]` | `dist/web`: the game with JS and fonts inlined, ready for any static host |
| `make_exe.py [--out DIR]` | `dist/RetroSurvivors/RetroSurvivors.exe` (Electron + the game), from Windows or Linux |
| `make_appimage.py` | `dist/RetroSurvivors-<v>-x86_64.AppImage`, from Windows or Linux |
| `make_apk.py` | `dist/RetroSurvivors-<v>.apk` (WebView app, `tools/android/`), from Windows or Linux |
| `make_manual.py [fr\|en\|es]` | the player booklets `manual/RetroSurvivors_Manual_<FR\|EN\|ES>.pdf` from content.json (re-run on releases) |
| `bump_build.py 0.xx` | sets `BUILD` in `game/js/assets.js` and the `?v=` of the scripts in `game/index.html` |
| `strip_meta.py` | removes ID3 / EXIF metadata from the game's media, byte-wise (audio frames untouched) |
| `publish_github.py [--dry-run] [--private-only] [--no-release] [--fresh-public-history]` | step-by-step commit and push of your changes, then of the public copy to BigFatDeuce/retro-survivors-game, then the version's builds and manuals on its Releases page (see `docs/PUBLISHING.md`) |
| `make_public.py [--out DIR] [--list]` | the public copy: committed files on its allow list (not the working notes `docs/HISTORY.md`, `docs/reports/`) + `docs/public/` (README, pictures, .gitignore), mirrored into `dist/public-repo`; refuses files over 100 MB, secrets, personal paths |

## Content — `tools/content/`

| tool | what it does |
|---|---|
| `patch_v20.py` | the base: applies v2.0 to `work/content_v19.json` (the published v1.9 content) |
| `patch_020.py` … `patch_098.py` | one per version, each imports the previous one and changes `C` in memory; only the one run as a script writes content.json. Their docstrings say what each version changed |
| `weapons060.py` | the 40 weapons (5 per type, real Retro names) |
| `fusions060.py` | the spell fusions (3 per class) and their damage factors `CAL` |
| `calib_fusions060.py [rounds]` | recomputes `CAL` in `fusions060.py` from the spell bench (`checks/sim_node.js BENCH=`) |
| `globals060.py`, `relics060.py` | global spells added in 0.60, the relics (bonuses from the real items in `work/sl.db`) |
| `dialogues060.py`, `credits079.py`, `anec068.py` | Dark Vlad / Goultard scenes, the credits, Musha's anecdotes — 7 languages each |
| `text46_[abcd].json` | the short descriptions of 0.46 (spells, passives, items…) in 7 languages, read by `patch_041.py` |
| `newzones20.py` | the Île des Naufragés and the helpers later zones use (`mon()`, `boss()`, `make_map`) |
| `kwaknest068.py` | the secret Kwak nest zone (data; its world is `assets/build_flat068.py kwaknest`) |
| `chouque097.py` | the treasure's Chouque (a pirate killed by Kack Sparo): his lines and his hints at the profile names (`**name**` drawn bold, quoted) |
| `frigost097.py` | the Île de Frigost zone after Grobe: its monsters, bosses, waves (imported by `patch_097.py`; its world is `assets/build_frigost097.py`) |
| `calc_amber081.py` | computes the amber XP curve (`run.amber`) — computed, not simulated |

To change content: add the change to the newest patch if it belongs to the version being prepared, or create
`patch_<new version>.py` (copy the header of `patch_098.py`: `import patch_098 as P`, `C, G, T, put_ui = P.C, …`,
the `if __name__ == '__main__':` dump at the end). UI strings: `put_ui({'key': T(fr, en, de, es, it, nl, pt)})`. Never
edit content.json by hand: the next run overwrites it.

## Asset builders — `tools/assets/`

Characters (class sheets: base picture with colour zones black + RGB mask, accessory anchors):

| tool | what it does |
|---|---|
| `build_chars20.py 4.8 <keys>` | the class sheets' renderer; also the library the character tools share (`make_patch`, `hat_differs`…) |
| `build_move060.py chars\|pets\|bosses\|all [keys]` | 60-fps runs (`<sid>_r`) from the up-to-date client, pets' walks, humanoid bosses' walks (`_w60`) |
| `build_still063.py [key…]` | standing / cast / hit / death poses (`<sid>_s`) with exact anchors |
| `build_wfront060.py [sid…]` | weapon blows (`<sid>_x`) and their front layers (what the client paints over the weapon) |
| `build_accfront061.py [sid…]` | front layers of capes (`SLOT=2`) / hats (`SLOT=1`) for the `_r` and `_s` sheets (`SHEET=_s`) |
| `build_emote23.py ZOOM anim… [sid…]`, `build_emoteanc45.py` | emote sheets (`<sid>_e`) and their accessory anchors |
| `fix_flash061.py` | replaces the client's white flash frames of weapon blows (re-run after rebuilding `_x` sheets) |
| `remask091.py [key…]` | re-renders the colour masks losslessly in place (lossy masks made colours shimmer) |
| `shield_anc092.py`, `shield_back094.py` | shield anchors (slot 4) in every sheet; the back-run fix |
| `ancfill091.py [sid]` | rebuilds anchors a client clip lacks (used for the Otomaï) |
| `build_otomai091.py` | the Otomaï's icons, fusion icons, sounds, scale |
| `build_emblems30.py [A]` | class emblems `b1..b15` |

Accessories (`game/assets/acc/i/<sym>.webp`, one picture per accessory, `SPR.acci`):

| tool | what it does |
|---|---|
| `build_acc060.py new [sym…] \| weapons sym… \| icons` | accessories from the up-to-date client / weapon looks / their shop pictures; holds the helpers the accessory tools share (`frame_labels`, `libs`, `render`) |
| `capefix091.py sym:view…` | re-renders one view of an accessory (e.g. a cape's run), the other views kept |
| `acccolor091.py [sym…]` | the parts of accessories painted in the character's colours (masks) |
| `build_shields092.py [sym…]` | the 276 shields' looks and shop pictures |
| `build_blood060.py` | the bloody look of the Soif de Sang weapons |

Monsters, NPCs, effects:

| tool | what it does |
|---|---|
| `build_mobs20.py gfx[:boss][:z=Z]…` | monster sheets from client sprites (then `pack_mobs20.py --keys=…`) |
| `hd_mobs51.py render\|pack\|all` | re-renders every standard monster sheet in HD, then packs |
| `pack_mobs20.py [--dry] [--keys=…]` | packs sheets by the set of zones using them |
| `build_coloured52.py gfx key zoom colours [art]` | a monster in its sl.db colours (+ bestiary art) |
| `build_npc57.py [zoom]` (env `GFX`, `ANIMS`) | a scene character in HD (ToT `1010_z80`, Musha `1153_z120`) |
| `fix_coffre060.py`, `fix_sounds27.py [gfx…]` | the Coffre Animé's walk hop; sounds of monsters that had none |
| `build_fx060.py n…`, `build_fxhd061.py id:zoom…` | spell effect sheets from client spell clips; HD re-renders |
| `build_fist073.py`, `build_moon34.py`, `fix_whip54.py` | Frappe du Craqueleur's fist, Marteau de Moon (fx + icon), the cleaned whip |
| `build_aura20.py` | the idle auras (levels 100 / 200) |

Icons and interface (atlas `icons3*.webp`; `build_icons20.merge` adds pictures to it):

| tool | what it does |
|---|---|
| `build_icons20.py [it_T_G…]` | HD item pictures from the client's vector items; the `render` / `merge` library of every icon builder |
| `build_iconhd091.py [skins\|dofus\|relics\|gift\|gosword]` | item pictures shown big: skins 400 px (`assets/ui/hd/`), Dofus 440, relics 400, Nowel's gift 512, GO!'s Épée Royale du Bouftou 640 |
| `build_spellicons21.py`, `build_fusionicons060.py`, `build_globalicons23.py`, `build_globalicons060.py` | class spell icons, fusion icons (`build_fusionicons060.py [fusion id…]`: only those), global spell icons (23: the first ones, 060: the three of 0.60 and 0.96's Boule de Chaos; `[key…]`: only those) |
| `build_staticons34.py`, `build_staticons48.py`, `build_staticons068.py`, `build_demulti54.py` | characteristic / effect icons: client vectors (34), framed SVG ones (48), the up-to-date client's stats window (068), Démultiplication |
| `build_challenge20.py n…`, `build_ui060.py`, `build_ready060.py`, `build_zaap56.py`, `build_totbg41.py` | challenge pictures, small UI pictures, the 'ready' swords, ToT's zaap, ToT's quiz background |
| `build_retronum085.py font.ttf` | the client's damage-number font (`assets/fonts/retronum.woff2`) |
| `build_verdance098.py [Verdance-Bold.ttf]` | the announcements' font `assets/fonts/verdance.woff2` (Verdance Bold from `raw/fonts/verdance/`, + the accents, ß, Œ and punctuation it lacks, drawn in its style) |
| `build_cinzel095.py Cinzel[wght].ttf` | the announcements' font `assets/fonts/cinzel.woff2` (Cinzel, OFL: weights 700–900, the 7 languages' Latin subset) |
| `build_phoenix36.py` | the death screen's Phoenix statue (the original picture upscaled with `lib/esrgan.py`) |
| `build_boosters38.py`, `boosters/build_boosters.py` | the booster pack atlas from the original pictures; a standalone generator of booster designs (`dist/boosters/`) |

Bestiary, cards, worlds, sound:

| tool | what it does |
|---|---|
| `build_art21.py [A] [+gfx,…]`, `build_art38.py [gfx…]`, `build_ttg34.py` | bestiary artworks from client vectors / from the sprite when there is no artwork; TTG cards. Never stop `build_art21` during its repack (it deletes the atlases first: `git checkout -- game/assets/art/`) |
| `RES=3.0 build_worlds20.py <world>…` | worlds rendered from client maps (4096-px tiles + `SPR.worlds`); `build_vlad51.py`, `build_grobe54.py`, `build_flat068.py zone…` compose the hand-made plains; `build_frigost097.py` the Île de Frigost (laid out by hand in quarters from the client's snow pieces, toned down) |
| `decormask087.py <world>\|all` | each world's decor mask and depth map (ground effects under the scenery, characters behind trees) |
| `build_minis071.py [world…]` | the zones' mini maps |
| `build_sfx060.py [music names]` | sound effects (and whole music tracks) from the up-to-date client |
| `music55.py` | encodes the source music files (`work/music_src/`, not versioned) with ffmpeg |

## Shared modules — `tools/lib/`

| module | what it does |
|---|---|
| `swflib.py`, `timeline.py` | minimal SWF reader / writer; display-list simulation of SWF sprites |
| `stage.py` | renders SWF symbols to PNG frames with FFDec (`ffdec/`, needs Java 17+) |
| `maprender.py` | Dofus maps rendered from the client's vector graphics (cells, symbols, `work/symcache`) |
| `sprio.py` | the only safe way to update `game/data/sprites.json` |
| `release.py` | what the build scripts share: version, Electron version, shipped game files, cached downloads |
| `lang2json.py`, `langdata.py` | client lang files → `work/lang_json/`; the official names per language |
| `sl2db.py` | StarLoco SQL dumps → `work/sl.db` (maps, monsters, spells, items) |
| `sndanim27.py gfx…` | the sound keys each animation of a client sprite calls |
| `esrgan.py`, `upscale.py` | AI ×4 upscale (torch / ncnn) — only for pictures that exist as small bitmaps only |

## Research — `tools/research/`

| tool | what it does |
|---|---|
| `acctruth061.py`, `acccompare061.py`, `accuncover062.py`, `accheads062.py` | the client's own composition of a character with an accessory vs the game's (IoU, shifts, hair under hats) |
| `accanchor061.py`, `accselect061.py`, `accfix061.py` | the anchor and origin corrections derived from those measurements (they write sprites.json) |
| `findworld.py`, `findall.py` | find which client maps make an existing world picture (`work/world_<name>.json`) |
| `zonestats068.py`, `classcolors091.py`, `crack_maps51.py` | what a zone's maps are made of; each class's base colours; maps whose sl.db key is wrong |

## Tests — `tools/checks/`

| tool | what it does |
|---|---|
| `qa_unit.js`, `qa_spells.js` | node: data integrity, saves, rules; every spell does what it says (run by `qa.py`) |
| `qa_func.py`, `qa_web.py` | browser functional tests on a fresh profile; the deployed site, read only |
| `pw_test.py <script> <outdir>` | runs one `tests/t_*.py` Playwright script against a local server (env VW, VH, DPR, MOBILE, LG) |
| `stress.py [scenario…]` | crashes, frozen states, memory growth, stutters (`docs/TESTING.md`) |
| `perf_probe.py [--n 380] [--cpu 4] [--fx min] [--q sd] [--profile]` | a fixed heavy scene: frame time (update / draw), fps, top functions by self time |
| `perf_probe.py --each spells\|weapons\|systems [--only id,…] [--profile]` | every spell / weapon / run system alone over the same crowd: extra main-thread time, entities, 2D layers / boxes sent to the GPU (`work/perf/`) |
| `sim_node.js <cls\|all> <map> <minutes>` | headless simulator of the real game logic (balance sims, `BENCH=`, `AUDIT=1`) |
| `bench_draw.py` | micro-bench of drawing small bitmaps in Chrome |

## Retired and merged tools (0.94 cleanup)

Removed because their output format no longer exists or another tool does the job; they stay in Git history
(`git log --all -- tools/<name>.py`):
- `tools/legacy/` (v1.4–v1.9 scripts, unused since v2.0), `final2.py` (empty).
- `build_acc20.py` (v2.0 accessory sheets `acc*`/`accm`, replaced by per-accessory pictures in 0.60 — running it would
  have deleted `game/assets/acc/` and `SPR.acci`; its helpers moved to `build_acc060.py`), `build_accfix27.py` and
  `build_weapons23.py` (wrote into those retired sheets; now `capefix091.py` / `build_acc060.py weapons`),
  `build_hatback44.py` (patched the retired `acc4` sheet).
- `build_runfb40.py` (20-fps runs, superseded by `build_move060.py`), `build_art20.py` (superseded by `build_art21.py`),
  `hd_gfx52.py` (map decor upscale, dropped in 0.52), `build_sounds.py` (needed scripts that never were in
  the repository; sounds come from `build_sfx060.py` / `fix_sounds27.py`).
- Merged: `build_musha47.py` → `build_npc57.py` (`GFX=1153 ANIMS=staticR,bonusR,anim1R,anim2R … 12`);
  `build_dofus38.py`, `build_relics061.py`, `build_gift091.py` → `build_iconhd091.py dofus|relics|gift`.
- Root scripts: `jouer_local.*` → `play_local.*`, `publier_cloudflare.bat` → `publish_cloudflare.*`; the Windows build's
  logic moved from `make_exe.bat` / `make_exe.sh` into `make_exe.py`.
