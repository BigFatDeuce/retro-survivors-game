# Building and publishing

Every script below is at the repository's root, in a Windows (`.bat`, double-click it) and a Linux (`.sh`) version
that do the same thing; the work itself is done by the Python tool named in each script. Each one stops with
`FAILED` and a non-zero exit code when a step fails (a double-clicked window stays open so you can read it).
Requirements: Python 3.8+ (Windows: tick "Add Python to PATH" when installing it), plus what each line says.

| script | result | needs |
|---|---|---|
| `play_local` | plays the current files in your browser (local server, first free port from 8765, no cache) | Python |
| `make_exe` | `dist/RetroSurvivors/RetroSurvivors.exe` — the Windows game, nothing to install (`tools/make_exe.py`) | Internet the first time (Electron, kept in `dist/cache`); on Linux, `wine` sets the exe's icon |
| `make_appimage` | `dist/RetroSurvivors-<version>-x86_64.AppImage` — the Linux game (`tools/make_appimage.py`) | Internet the first time; on Linux `mksquashfs` if installed |
| `make_apk` | `dist/RetroSurvivors-<version>.apk` — the Android app (`tools/make_apk.py`) | Internet the first time (Google's build tools after you accept their licence, a JDK if missing) |
| `publish_cloudflare` | builds `dist/web` and **publishes it** on Cloudflare Pages | Node.js; a Cloudflare login the first time |
| `publish_github` | commits and pushes your changes to GitHub, then the public copy to the public repository, asking before each step | Git |

Notes:
- The version shown in the game and used in file names is `BUILD` in `game/js/assets.js`: set it with
  `python tools/bump_build.py 0.xx` (it also updates the `?v=` of the scripts, so browsers never mix two versions).
- Close the game before `make_exe`: a running `RetroSurvivors.exe` locks its folder. Its saves live in
  `%APPDATA%\Retro Survivors` and are never touched by the builds.
- The APK's signing key is `~/.retro-survivors/android.keystore` (Windows: `%USERPROFILE%\.retro-survivors\`): keep
  it; updates must be signed with the same key. On the phone, copy the `.apk` and open it (allow unknown apps).
- On the Linux PC, `chmod +x` an AppImage copied from Windows, then run it.
- Builds ship every file of `game/` except leftovers (`*.tmp`, `*.part`, locks, backups; `tools/lib/release.py`).
- The Electron version of the desktop builds is `ELECTRON` in `tools/lib/release.py`.

## Publish your changes to GitHub — `publish_github`

The source lives in the private repository **BigFatDeuce/retro-survivors** (branch `main`). To send your local
changes there, double-click `publish_github.bat` (Windows) or run `./publish_github.sh` (Linux). It works from any
folder inside the repository and uses your own Git setup: remotes, branch, upstream and saved credentials. It stores no
password or token.

What it does, step by step — nothing is changed before you confirm:
1. Checks Git, the repository, and that no merge / rebase / conflict is in progress and you are on a branch.
2. Shows the branch, the remote and how many commits are waiting to be pushed or pulled; it runs `git fetch` (this
   never changes your files). If the remote has commits you do not have, it offers `git pull --ff-only`, which never
   rewrites anything; if your branch and the remote have diverged, it stops and explains.
3. Lists the changes: files already staged, modified / deleted tracked files, new files. New files that look like
   secrets, caches or build outputs (`.env`, keys, `*.tmp`, `*.log`, `dist/`, `__pycache__/`…) are left out and
   listed; files over 100 MB (GitHub's limit) stop the script.
4. You choose: all tracked changes, one by one, a summary of the changes (`d`) or the full diff (`f`), and which new
   files to add (none by default).
5. It shows exactly what will be committed and asks for a message (Enter keeps the default `Update <date>`), then asks
   before committing.
6. It lists the commits to push and asks before `git push` (`git push -u <remote> <branch>` the first time). It also
   pushes commits you made earlier, without creating an empty commit.

It never force-pushes, never deletes or resets anything, never changes your remotes (but `--fresh-public-history`, below).
`--dry-run` shows what would be done without staging, committing, fetching or pushing.

### The public repository — BigFatDeuce/retro-survivors-game

After the push above, the script offers to update the public repository (its address is this repository's with
`-game`; `--private-only` skips this part):
1. The first time, it clones it into `dist/public-repo/` (ignored here); afterwards it gets any commit made on GitHub's
   site (`git pull --ff-only`).
2. `tools/make_public.py` writes the public copy into that clone: the **committed** files on its allow list — `game/`,
   `tools/` (not `research/` nor the publishing tools), `tests/`, `docs/` (not `docs/public/`, nor the working notes
   `docs/HISTORY.md` and `docs/reports/`), the `make_*` /
   `play_local` scripts, `.gitattributes`, and the data the content chain reads (`work/*.json`, `work/sl.db`,
   `work/lang_json/`, `work/lang_new/`) — plus `docs/public/README.md` as `README.md`, `docs/public/media/` as `media/`
   and `docs/public/gitignore` as `.gitignore`. Files that left the list are deleted there; `LICENSE` (MIT, made on
   GitHub) is kept. Never copied: `raw/`, `ffdec/`, the builders' material in `work/`, `manual/`, `CLAUDE.md`, this
   repository's README and `.gitignore`, uncommitted changes.
3. It refuses (nothing committed) a file over 100 MB, a file that looks like a secret, a text holding the maintainer's user
   name or e-mail address.
4. It shows the changes, asks for the commit message (Enter = `Retro Survivors <version> (<this repository's commit>)`),
   then before committing and before pushing — one commit per publication, so the public history starts clean.

To see what would go out without writing anything: `python tools/make_public.py --list`. The public page itself
(features, pictures, how to build) is `docs/public/README.md`: edit it here, it goes out with the next publication.
### The Releases page (downloads)

The installed games (exe, AppImage, APK) read this page: at launch (at most every 6 h, `C.update`), when a release
newer than their version is there (pre-releases count, drafts do not), the main menu shows a window once a day and a
"Version x available" button; it opens the release's page. So a release must be complete when it is published.

Last, the script offers the public repository's **Releases** page for the version in `game/js/assets.js`:
- the files: `dist/RetroSurvivors` zipped as `RetroSurvivors-<v>-windows.zip` (an existing `dist/RetroSurvivors-<v>.zip`
  is used when it is of that version and newer than the folder), `RetroSurvivors-<v>.apk`, `RetroSurvivors-<v>-x86_64.AppImage`,
  and the three manuals; a build of another version is not offered, and a build older than the last committed change
  to `game/` is flagged (rebuild it first if that change should be in);
- the release `v<version>` is created (a pre-release, the beta) with the changelog's section of that version and how to
  install on each system (0.97: the game's French names in it — spells, classes, monsters, zones, items — become their
  official English names from content.json, `english_names`; the accented words left are listed on screen); when it exists, only the files it lacks are sent (an upload cut off is sent again);
- the login: GitHub CLI (`gh`) when installed, else the one Git already keeps for github.com (Git Credential Manager),
  never shown nor saved. If GitHub refuses it: `winget install GitHub.cli`, `gh auth login`, run again.
About 3 GB to send for a full release: it takes a while. `--no-release` skips this part.

Common problems:
- **"The remote has commits you do not have"**: someone (or another PC) pushed. Accept the `git pull --ff-only`, check
  the game still works, run the script again. If it says the branches have diverged, ask for help or run
  `git pull --rebase` yourself, then run the script again. Never force-push.
- **GitHub refused your credentials**: on Windows the Git Credential Manager opens a sign-in window — sign in again;
  or run `gh auth login`. Your account must have write access to the repository.
- **A merge / rebase is in progress, or conflicts**: finish it (`git status` says what to do) or abort it
  (`git merge --abort`, `git rebase --abort`), then run the script again.
- **You are not on a branch (detached HEAD)**: `git switch main` (your files are kept).
- **You staged something by mistake**: answer `n` to "Keep these staged files", or run `git restore --staged <file>`
  (your file is not changed).
- **A file is too big**: leave it out or add it to `.gitignore`.
- To look at the changes yourself first: `git status`, `git diff` (tracked changes), `git diff --cached` (staged).

### Restarting the public repository from one commit — `publish_github_fresh`

`publish_github_fresh.bat` / `.sh` (= `tools/publish_github.py --fresh-public-history`) publishes like `publish_github`,
but the public repository then holds **one** commit with the current public copy: its old commits are replaced (forced
push), and its old releases and tags are deleted from GitHub, after you type `RESET`; the version's release is made
again from the builds in `dist/` (rebuild them first: older builds carry older files). The private repository is
published as usual. For a one-off clean-up (0.96: the public copy no longer carries the working notes, and the code's
comments were rewritten): use `publish_github` afterwards. Clones and forks made before keep their copies; GitHub may
show an old commit to someone holding its exact link until its cache expires (GitHub Support can purge it).

## Publish the web version — Cloudflare Pages

The game is a static site: Cloudflare Pages hosts it for free (≈ 2 500 files of the 20 000 allowed, none over 25 MB).
`publish_cloudflare` builds `dist/web` (`tools/make_dist.py`: the game with its scripts and fonts inlined) and uploads
it with `npx wrangler@3 pages deploy` to the project `retro-survivors` (branch `retro-survivors`). **It publishes to
everyone without asking**: run it when the version is ready (after the release procedure in `docs/TESTING.md`).

First time on a PC:
1. Install Node.js (LTS) from <https://nodejs.org>.
2. Run `publish_cloudflare`. A web page opens: log in to Cloudflare and click **Allow**. If it asks to create the
   project `retro-survivors`, accept.
3. At the end it prints the address (`https://retro-survivors.pages.dev` or the custom domain).

Custom domain: Cloudflare dashboard → **Workers & Pages** → `retro-survivors` → **Custom domains** → **Set up a custom
domain** (a domain bought at Cloudflare is linked at once; one bought elsewhere needs its DNS servers moved to
Cloudflare). The current site is <https://retro-survivors.holy-c.men/>.

Roll back: project → **Deployments** → the version wanted → **Rollback**. Players' saves stay in their browsers, and
the `?v=BUILD` of every file keeps browsers from mixing two versions.

Keep in mind: the game uses the Dofus Retro client's files (Ankama's property). A public site exposes them; the GitHub
repository stays private, only `dist/web` goes to Cloudflare.
