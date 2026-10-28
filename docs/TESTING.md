# Testing

One command runs every automated test, in two sizes:

```
python tools/qa.py quick                  (~5 min: before every commit that touches game/)
python tools/qa.py full                   (~1 h 30: before every release)
python tools/qa.py full --web             (+ the deployed site, read only)
python tools/qa.py quick --only spells,unit    (some steps only; python tools/qa.py --list prints them)
```

Report: `work/qa/<date>-<suite>/report.md` (one line per step: PASS / FAIL / NOT-RUN and why), each step's log next to
it. Exit code 1 if a step fails. Steps run one after the other, never two at once (some measure the machine).
Shorter checks when you know what you touched:

| what you changed | run at least |
|---|---|
| game code (`game/js`, `index.html`) | `python tools/check.py` (~3 min); `python tools/qa.py quick` before committing |
| `Run.draw` or a draw function | + `python tools/checks/pw_test.py tests/t_pixicmp.py work/t_pixicmp` |
| menus / CSS | + `tests/t_uiaudit.py`, `tests/t_overlap.py` (phones), `tests/t_cards.py` (level-up cards) |
| the content chain | `python tools/make_content.py --check` before and after, then `node tools/checks/qa_unit.js` and `node tools/checks/qa_spells.js` |
| a sprite sheet | `tests/t_pixicmp.py`, then a look in game (`play_local`) |
| tools / scripts only | run the tool you changed; `python tools/make_content.py --check` if it is imported by the content chain |

Safety: every browser test starts from a **fresh profile** on a local server at a free port (never 8765 — the
the maintainer's own server —, never the player's saves, never the desktop exe, which uses the real saves); the deployed site
is only read (`tools/checks/qa_web.py`: pages, headers, nothing sent).

## What each step checks

| step | tool | checks |
|---|---|---|
| unit | `tools/checks/qa_unit.js` (node, ~15 s) | content references (spells, fusions, monsters, bosses, sheets, effects, icons, sounds, music, skins, shields, achievements), files with their exact case (web servers are case-sensitive), texts in 7 languages, media without metadata, saves (old, partial, damaged, import accepted / refused, save code round trip, separate profiles), rules (stats recomputed identically, shield +1 once, drops not overlapping), every class / zone / spell / weapon run without error |
| spells | `tools/checks/qa_spells.js` (node, ~15 s) | every spell, fusion and global spell does what it says: cast alone at max level on fixed targets, its effects seen (damage, slow, stun, poison, burn, mark, heal, armour, pull, summon, life steal, bounce, kamas), cast rhythm = cooldown, areas within their radius, projectile counts; the words of its description must be visible in its effects. Seeded randomness: same result every run. Balance is NOT judged |
| func-core | `tools/checks/qa_func.py` (browser, real GPU) | boot, damaged saves at boot, import, keyboard / mouse / simulated controller navigation, shop (price taken once, refusal without kamas, kept after reload, shield in runs), runs (countdown, level-up card, boss, pause, give up, death then Replay, cancelled run, victory, what is saved; after each run no timer, sound or loop left) |
| t_save | `tests/t_save.py` | export / import through the options, refusal of a file that is not a save |
| check | `tools/check.py` | the 0.59 safety net: simulations + 4 bot runs (PixiJS and Canvas 2D), no page error, no `Game._frameErr`, no missing file, load times, fps |
| func-more | `tools/checks/qa_func.py` | 6 runs in a row (nothing accumulates), settings kept (volumes, language, quality, Canvas 2D), profiles, 6 PC screen sizes |
| t_freeze, t_tmap, t_levelup, t_cards, t_noscroll, t_uiaudit | `tests/` | every zone started through the real menus keeps moving; treasure maps; level-up cards fit; scrolling; every menu at 6 PC sizes + phones |
| t_overlap | `tests/t_overlap.py` | every menu, tab and window on 6 phones (3 upright, 3 sideways): overlapping texts / pictures / buttons, cut texts, squeezed lists; screenshots circled in red |
| t_pixicmp | `tests/t_pixicmp.py` | the same frozen scene in PixiJS and Canvas 2D, mean difference ≤ 3 / 255 |
| stress | `tools/checks/stress.py --reps 1` | memory, leaks, stutters (below) |
| canvas2d, edge | `tools/checks/qa_func.py` | runs on the Canvas 2D renderer; boot, saves and runs in Microsoft Edge |
| web | `tools/checks/qa_web.py` | the deployed site: first load (HTTP errors, console), cache, one run, every requested file (exact case), deployed vs local version |

One Playwright script by hand: `python tools/checks/pw_test.py tests/t_smoke.py <outdir>` (env `VW`, `VH`, `DPR`,
`MOBILE=1`, `LG=<language>`, `PORT`). A test script receives `pg` (the Playwright page), `url(query)`,
`shot(name, clip=…)`, `out`; it can drive the game with `pg.evaluate("…")` (`Game.run.spawnBoss(...)`,
`UI.levelUpMenu(R, opts)`…). Keep test scripts ASCII (escapes): `pw_test.py` reads them in the system code page on
Windows.

## Simulator and benches

- `node tools/checks/sim_node.js <cls|all|a,b> <map> <minutes>`: the real game logic headless with a bot (env `GOD=1`,
  `DODGE=1`, `HARD=1`, `SHOP=n`, `XP=1`, `ALLXP=1`, `HEAL=1 IDLE=1`, `GAME_C=<other content.json>`).
- `AUDIT=1 [VERBOSE=1] node tools/checks/sim_node.js x x 11`: every class on every zone for 11 minutes, errors with
  stack, drop / event totals, then every characteristic, relic and Dofus applied alone must move a stat.
- `BENCH=all|weapons|id,… [LV=1,4] [DUR=90] node tools/checks/sim_node.js x astrub 0`: damage per second of each spell
  alone. Single runs are noisy (±30 %). Balance is a design decision, not a bot run's.
- `python tools/check.py --bench[=poison|numbers|pixi]`: 200 monsters on screen at CPU ×1 / ×4 (`UNCAPPED=1` lifts the
  screen's refresh cap, `SOFT_GPU=1` = SwiftShader ≈ a weak PC). Compare rows of one session, not runs of different days.

## Stress — `tools/checks/stress.py`

Looks for crashes, frozen states, growing memory and stutters, in Playwright's Chromium on the real GPU, from a fresh
profile, with `Math.random` seeded.

```
python tools/checks/stress.py                          (every scenario, 3 repetitions)
python tools/checks/stress.py charswap --reps 10       (the 0.92 crash: character changes)
python tools/checks/stress.py --quality uhd --reps 2   (sd, hd, uhd, k4)
python tools/checks/stress.py --renderer canvas runs
python tools/checks/stress.py --replay work/stress/<date>/log.json     (same seed, size, renderer)
```

Options: `--seed` (1234), `--max-min` (40), `--size 1920x1080`, `--soft-gpu`, `--out`. Report:
`work/stress/<date>/report.md` + `log.json`. An interrupted or incomplete scenario is a **failure**, never a pass.

## Performance — `tools/checks/perf_probe.py`

One fixed heavy scene (~320 monsters, 3 bosses, the class's five spells at the top level, the character immortal):
prints one JSON line (frame JS median / p95 split into update / draw, fps) and with `--profile` the top functions by
self time and the natives by caller. `--cpu 4` = Chrome's CPU throttling (a weak PC / a phone's main thread),
`SOFT_GPU=1` = SwiftShader (a weak GPU: fill-bound), `--fx full|low|min`, `--q sd|hd|uhd|k4`. Compare lines of one
session only (the machine's load moves). 0.95 reference at CPU ×4, 1440p: 9.6 / 7.8 / 7.2 ms for full / low / min.
`--each spells|weapons|systems` goes through every spell (class spells with their class, fusions, global spells), every
weapon or the run's systems (bosses, elites, Archimonsters, statuses on the whole crowd, random events…) one at a time
over the same crowd (no waves, no level-ups, the character untouchable) and sorts them by the main-thread time they add;
`LAYERS` / `boxes` = full-screen 2D layers / small 2D boxes sent to the GPU per frame (the PixiJS path's costliest
fallback: keep them near 0). Never run two browsers at once while measuring (the numbers move by 50 %).

| scenario | does |
|---|---|
| `menus` | every menu and tab, back, again |
| `charswap` | play screen, 10 character changes, shop preview classes, Astrub from the menus, 20 s of play, give up — in a loop |
| `runs` | runs in a row over light / heavy classes and zones, ended by giving up, death or victory |
| `fight` | 260 monsters, maxed spells, a boss, damage numbers |
| `pause` | fast pause / resume, hidden tab, key bursts |
| `firstuse` | the first appearance of spells / effects in a session: frames over 50 ms it causes |

Measured per step: duration (cold / warm), JS heap after forced GC, DOM nodes and listeners, the renderer / GPU
processes' private memory (Windows; an indirect indicator), the game's counters (`CharSprite.live`, decoded images,
PixiJS sources, caches), frame times p50 / p95 / p99, frames over 33 / 50 ms and the script Chrome blames for each,
page errors, `Game._frameErr`, lost WebGL contexts.

## Manual checks (a person, before a release)

- A real controller (buttons, rumble, sticks) and a real phone (touch, rotation, sound, battery); the APK on a phone.
- The Windows exe and the AppImage (F11, closing, saves in the user profile).
- Sound by ear (relative volumes, music changes, no crackle); new visuals at 1080p / 1440p / 4K.
- Not possible on the development PC: Safari / iPhone, Firefox, other GPUs, players' networks.

## Release procedure

1. `python tools/qa.py full --web` → every step PASS (or each FAIL explained in the report).
2. The manual list above.
3. `python tools/bump_build.py 0.xx`, then the builds (`make_exe`, `make_appimage`, `make_apk`) and the manual
   (`python tools/make_manual.py`); publish (`docs/PUBLISHING.md`).
4. After publishing: `python tools/qa.py quick --only web --web` (the site serves the new version).

## Regressions watched by the tests

| defect | test |
|---|---|
| crash after ~10 character changes (0.93) | stress charswap |
| boot blocked by a damaged save (0.94) | qa_unit store, qa_func saves / import |
| volume slider of a closed screen still changing (0.94) | qa_func nav |
| highlight lost after Escape / B (0.94) | qa_func nav |
| listeners / timers left after a run | qa_func runs / restart, stress |
| shield +1 counted twice, worn by the Roublard | qa_unit logic, qa_func shop |
| a spell no longer applying its effect (fault injection done) | qa_spells |
| overlapping menus on phones (0.94) | t_overlap |
| the test's death ignored after a monster's touch (0.95: `stress.KILL`) | qa_func runs, stress |
| a death that never ends behind a window the bot left open (0.96: `close_windows`) | qa_func runs, stress |
| a scroll counted on a window that cannot scroll (0.95: the corner diamonds) | t_levelup (overflow auto / scroll only) |

Performance references (RX 9070 XT, 1080p, PixiJS): median frame 6–7.5 ms (p99 8.6), page memory 1.6–2.2 GB stable over
40 character changes, a run loads in 1.8–2.2 s (the reports, `docs/reports/`, are in the private repository).
