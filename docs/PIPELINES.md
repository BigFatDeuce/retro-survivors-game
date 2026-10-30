# Content and asset pipelines

Everything in `game/data/` and `game/assets/` is generated from the Dofus Retro client by the tools in `tools/`
(index: `tools/README.md`). This page explains the sources, the two pipelines and the traps. Per-system history and
decisions: `docs/HISTORY.md` (private repository).

## Sources

| where | what | versioned |
|---|---|---|
| `raw/rc/` | the Dofus Retro **1.41.9** client's files (`clips/`, `data/maps/`, `modules/`, `audio/`…), copied from `<Retro install>/resources/app/retroclient/` at the time. Most builders read it (`_root.RAW`) | yes (Ankama's property: the repository must stay **private**) |
| the installed client | the **up-to-date** official client (60-fps sprites = the Remastered ones, newer skins, shields, sounds), read in place from `%LOCALAPPDATA%/Ankama/Retro/resources/app/retroclient` (`_root.CLIENT`; override with `RS_NEWCLIENT`). Needed by `build_move060`, `build_still063`, `build_acc060 new`, `build_sfx060`, `shield_anc092`, `build_staticons068`, `build_ready060`, the accessory research tools | no (installed by the Ankama launcher) |
| `work/sl.db` | the StarLoco emulator database as SQLite (maps and their keys, monsters, spells, items, drops) — `tools/lib/sl2db.py` | yes |
| `work/lang_json/` | the official lang files as JSON, 7 languages (`tools/lib/lang2json.py`) | yes |
| `work/content_v19.json` | the published v1.9 content, base of the content chain | yes |
| `work/world_<name>.json`, `mapinfo.json`, `symindex.json`, `map_plain.json` | which client maps make each world; map index; symbol index; maps whose sl.db key was wrong | yes |
| `work/chars_v19/`, `acc_v19/`, `v19_worlds/`, `sprites_before_chars.json`, `mobs_prepack*` | v1.9 pictures the HD rebuilds match against / sit under | yes |
| `work/*.json` lists (`newskins060`, `shields092`, `classcolors091`, `ttg34`, `spell_sprites`…) | lists produced once by a tool and read by the content chain or builders | yes |
| `work/<tool>/`, `work/symcache/` | scratch renders and caches | no (rebuilt on demand) |
| `work/music_src/`, `work/retrolab/`, `aside/` | the music sources, the real-client capture lab, client files set aside | no (local only) |
| `ffdec/` | JPEXS FFDec 24.1.1 (CLI), renders SWF symbols — needs Java 17+ | yes |

Environment on a new machine: Python 3.8+ with `pip install pillow numpy opencv-python playwright` then
`playwright install chromium`; Node.js; Java 17+ (`java -version`); ffmpeg for audio tools. On Windows run Python
tools with UTF-8 (`python -X utf8 …` or `PYTHONUTF8=1`): the older ones open files with the system encoding.

## Content pipeline → `game/data/content.json`

```
work/content_v19.json → patch_v20 → patch_020 → patch_023 → … → patch_091 → patch_094 → patch_095 → patch_096 → patch_097 → patch_098 → content.json
                        (tools/content/; each imports the previous one and changes C in memory)
```

- `python tools/make_content.py` runs the newest patch (found by its number), which writes content.json.
  `python tools/make_content.py --check` builds it in memory and compares: **the chain must reproduce content.json
  byte for byte** (it does as of 0.94). Run `--check` before and after touching an older patch.
- A patch exposes `C` (the content), `G` (the game folder), `T(fr, en, de, es, it, nl, pt)` and `put_ui({key: T(…)})`;
  only `if __name__ == '__main__':` writes the file. Data too big for a patch lives in a data module next to it
  (`weapons060.py`, `fusions060.py`, `credits079.py`…).
- To change content: put the change in the newest patch when it belongs to the version being prepared, else add
  `tools/content/patch_<version>.py` that imports the newest one (copy `patch_098.py`'s header and footer). Describe the
  change in its docstring. Balance numbers are design decisions: change them only when asked.

## Asset pipeline → `game/assets/` + `game/data/sprites.json`

Vector symbols of the client's SWF files are rendered by FFDec at the zoom they are shown at (`tools/lib/stage.py`),
cropped, packed into atlases (≤ 4096 px) and described in `sprites.json` (written only through `tools/lib/sprio.py`).

| what | builder(s) | output |
|---|---|---|
| class sheets | `build_chars20` (base), `build_move060` (60-fps runs `_r`), `build_still063` (poses `_s`), `build_wfront060` (weapon blows `_x`), `build_accfront061` (cape / hat front layers), `build_emote23` + `build_emoteanc45` (emotes `_e`), `remask091` (lossless masks), `fix_flash061`, `shield_anc092` | `assets/chars/<key>.webp` + `<key>_m.webp`, `SPR.chars` |
| accessories | `build_acc060 new|weapons|icons`, `capefix091`, `acccolor091`, `build_shields092`, `build_blood060` | `assets/acc/i/<sym>.webp`, `SPR.acci` |
| monsters | `build_mobs20`, `hd_mobs51`, `pack_mobs20`, `build_coloured52`; scene NPCs `build_npc57` | `assets/mobs/`, `SPR.mobs` |
| spell effects | `build_fx060`, `build_fxhd061`, `build_fist073`, `build_moon34`, `fix_whip54`, `build_aura20` | `assets/fx/`, `SPR.fx` |
| icons | `build_icons20` (+ `merge`), `build_iconhd091`, `build_spellicons21`, `build_fusionicons060`, `build_globalicons*`, `build_staticons*`, … | `assets/ui/icons3*.webp` (pages), `icons2.webp`, `ui/hd/` |
| bestiary, cards | `build_art21`, `build_art38`, `build_ttg34` | `assets/art/`, `assets/ttg/` |
| worlds | `build_worlds20` (client maps), `build_vlad51`, `build_grobe54`, `build_flat068`, `build_frigost097` (composed plains), `decormask087`, `build_minis071` | `assets/worlds/<world>_<x>_<y>.webp` (4096-px tiles), `_decor` / `_depth` masks, `SPR.worlds` |
| sounds, music | `build_sfx060`, `fix_sounds27` (+ `lib/sndanim27`), `music55` | `assets/audio/`, `data/sounds.json` |

Order for a class sprite rebuild (e.g. after a client change): `build_move060 chars <sid>` → `build_still063 <sid>` →
`build_wfront060 <sid>` → `fix_flash061` → `SHEET=_s|_r SLOT=1|2 build_accfront061 <sid>` → `remask091 <keys>` →
`shield_anc092 <keys>`; then a look in game.

### Worlds (the most delicate pipeline)

- A zone = a block of Dofus maps (742 × 432 Dofus px each) composed into one picture at `RES` px per Dofus px (3.0),
  cut into 4096-px tiles. `compose()`: backgrounds, ground cells (with margins against seams), each map again in its
  window with a wavy cross-fade (`seam_alpha`), `fix_ground`, `blend_open_sea`, then objects sorted by depth.
  Dofus cell geometry: CW 53, CHW 26.5, CHH 13.5, LH 20.
- `WATER` worlds redraw their water from the client's own pieces (`client_water`); the slow-water mask is
  `SPR.worlds[w].water`. Vlad, Goultard, Grobe, Koalak, Otomaï jungle, Pandala, Nowel, Frigost and the Kwak nest are **composed
  plains** made of client pieces (`inset` keeps the player out of the forest border).
- `decormask087.py` writes each world's decor mask (tall objects: ground effects go under them) and depth map
  (characters behind trees) — the world builders call it for their objects.
- Decisions: no redrawn shores, softening only; never upscale map decor bitmaps (tried and dropped in 0.52).
- Check a world on full-resolution crops and in game: a thin black line every 4096 px on a reduced preview is the
  preview's rounding, not the game.

## Traps (already paid for)

- Never stop `build_art21` during its repack: it deletes the atlases first (`git checkout -- game/assets/art/`).
- Two builders writing `sprites.json` at once lost entries: run sheet builders one at a time; write it only through
  `sprio.update` (the icon atlas merge does too since 0.94).
- The up-to-date client plays clips at **60 fps** (the 1.41.9 one at 20): a clip has 3× more frames. Never render a
  fixed number of frames: read the real length (`eff_frames`, or the nested clip under a label) and keep the rate.
- FFDec with `-onerror ignore` writes nothing when a shape is invalid: run FFDec by hand on the SWF to see the error.
  A SWF shape edge is 17 bits at most (±65 535 twips): big shapes are split into segments.
- Client clips sometimes alternate empty frames or mix layers (the whip fx 211, weapon-blow flash frames): look at the
  frames before blaming the code.
- Masks must be lossless WebP (`BC.MASK_WEBP`): lossy 4:2:0 masks made the class colours shimmer.
- Atlases are capped at 4096 px: lower the zoom when a builder says "atlas too tall".
- Smoothing water "in strips along the seams" makes hard steps: use smoothed 2D fields.
- Icons shown bigger than their picture are re-rendered from the client's vector art, never redrawn or upscaled; an
  AI upscale (`lib/esrgan.py`) only for pictures that exist as small bitmaps only.
- `pkill -f pattern` from a shell whose command line contains the pattern kills that shell.
- The client's sound key table (AUEC) is empty in `work/lang_json`: a sound key not already in `sfx_pack.mp3` cannot be
  resolved yet.
