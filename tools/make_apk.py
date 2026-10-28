"""Retro Survivors -> an Android APK (a full-screen WebView playing the game's own files, nothing else), from Windows OR
Linux, like make_exe / make_appimage: nothing to edit on updates — the version comes from game/js/assets.js (BUILD), the
whole game/ folder is put in the APK.
  python tools/make_apk.py          (or make_apk.bat / make_apk.sh at the repo's root)
No Gradle, no Android Studio: the Android SDK's own build tools (aapt2, d8, zipalign, apksigner) and javac.
Downloads, the first time only (kept in dist/cache/android), when the PC does not have them already:
  - Android SDK build-tools + platform android-35 (Google, dl.google.com, ~110 MB) — their licence (Android Software
    Development Kit License Agreement) is shown and must be accepted by the person running the script
  - a JDK 21 (Eclipse Temurin, adoptium.net, ~190 MB) if javac is not found (only a JRE is not enough)
An installed SDK is used instead when found (ANDROID_HOME, ANDROID_SDK_ROOT, %LOCALAPPDATA%\\Android\\Sdk, ~/Android/Sdk).
Signing key: ~/.retro-survivors/android.keystore, made the first time (keep it: an update installs over the old APK —
keeping the saves — only when signed by the same key; with a new key the old app must be uninstalled first).
Result: dist/RetroSurvivors-<version>.apk — copy it to the phone and open it (allow 'install unknown apps' for the file
manager), or `adb install -r dist/RetroSurvivors-<version>.apk`.
Options: --accept-license (the SDK licence was read and is accepted: no question), --no-jdk-download"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, re, sys, glob, json, shutil, zipfile, tarfile, subprocess, urllib.request, xml.etree.ElementTree as ET, platform
import release as RL

G = f'{ROOT}/game'
CACHE = f'{ROOT}/dist/cache/android'
WORK = f'{ROOT}/dist/apk'
SRC = f'{ROOT}/tools/android'
API, BT = '35', '35.0.0'
REPO = 'https://dl.google.com/android/repository/'
JDK_URL = 'https://api.adoptium.net/v3/binary/latest/21/ga/{os}/x64/jdk/hotspot/normal/eclipse'
KEY = os.path.join(os.path.expanduser('~'), '.retro-survivors', 'android.keystore')
KEY_ALIAS, KEY_PASS = 'retrosurvivors', 'android'   # (a sideloaded fan game: the Android SDK's debug-key convention)
STORED = {'.webp', '.png', '.jpg', '.jpeg', '.mp3', '.ogg', '.woff2', '.woff', '.gz', '.zip'}   # (already compressed)
WIN = os.name == 'nt'
EXE = '.exe' if WIN else ''


def say(*a): print(*a, flush=True)


def version():
    m = re.search(r"const BUILD = '([^']+)'", open(f'{G}/js/assets.js', encoding='utf-8').read())
    if not m: sys.exit('version (BUILD) not found in game/js/assets.js')
    return m.group(1)


def fetch(url, dest, what):
    if os.path.exists(dest): return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    say(f'Downloading: {what}\n  {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'retro-survivors-build'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest + '.part', 'wb') as f:
        n = int(r.headers.get('Content-Length') or 0); got = 0
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b); got += len(b)
            if n: print(f'\r  {got >> 20} / {n >> 20} MB', end='', flush=True)
    print(); os.replace(dest + '.part', dest); return dest


# ---------------------------------------------------------------- the Android SDK pieces
def sdk_dirs():
    out = [os.environ.get('ANDROID_HOME'), os.environ.get('ANDROID_SDK_ROOT'), f'{CACHE}/sdk']
    if WIN: out.append(os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk'))
    out.append(os.path.expanduser('~/Android/Sdk'))
    return [d for d in out if d and os.path.isdir(d)]


def find_sdk():
    for d in sdk_dirs():
        bts = sorted(glob.glob(f'{d}/build-tools/*/'), key=lambda p: [int(x) if x.isdigit() else 0 for x in re.split(r'[.\-]', os.path.basename(p.rstrip('/\\')))])
        jars = sorted(glob.glob(f'{d}/platforms/android-*/android.jar'), key=lambda p: int(re.sub(r'\D', '', os.path.basename(os.path.dirname(p))) or 0))
        for bt in reversed(bts):
            if os.path.exists(f'{bt}/aapt2{EXE}') and os.path.exists(f'{bt}/lib/d8.jar') and os.path.exists(f'{bt}/lib/apksigner.jar') and jars:
                return bt.rstrip('/\\'), jars[-1]
    return None


def install_sdk(accept):
    """build-tools and the platform straight from Google's repository (what sdkmanager does), after the licence"""
    xml = fetch(REPO + 'repository2-3.xml', f'{CACHE}/repository2-3.xml', "la liste des paquets du SDK Android")
    root = ET.parse(xml).getroot(); loc = lambda e: e.tag.split('}')[-1]
    lic = next((e.text for e in root.iter() if loc(e) == 'license' and e.get('id') == 'android-sdk-license'), None)
    host = 'windows' if WIN else 'macosx' if sys.platform == 'darwin' else 'linux'
    urls = {}
    for p in root.iter():
        if loc(p) != 'remotePackage' or p.get('path') not in (f'build-tools;{BT}', f'platforms;android-{API}'): continue
        for a in p.iter():
            if loc(a) != 'archive': continue
            ho = next((x.text for x in a if loc(x) == 'host-os'), None)
            if ho and ho != host: continue
            u = next((x.text for x in a.iter() if loc(x) == 'url'), None); sz = next((x.text for x in a.iter() if loc(x) == 'size'), '0')
            if u: urls[p.get('path')] = (u, int(sz))
    if len(urls) < 2: sys.exit(f'packages not found in Google\'s list: {sorted(urls)}')
    if not accept:
        say('\n' + '=' * 78 + '\nAndroid SDK licence (Google) — read and accept it to download its build tools:\n' + '=' * 78)
        say((lic or '(text not found: https://developer.android.com/studio/terms)').strip()[:20000])
        say('=' * 78)
        a = input("Do you accept this licence? Type 'y' for yes: ").strip().lower()
        if a not in ('o', 'oui', 'y', 'yes'): sys.exit('Licence declined: nothing was downloaded.')
    sdk = f'{CACHE}/sdk'
    for path, (u, sz) in urls.items():
        z = fetch(REPO + u, f'{CACHE}/{u}', f'{path} ({sz >> 20} Mo)')
        dest = f'{sdk}/build-tools/{BT}' if path.startswith('build-tools') else f'{sdk}/platforms/android-{API}'
        if os.path.isdir(dest): shutil.rmtree(dest)
        tmp = f'{CACHE}/unzip'; shutil.rmtree(tmp, ignore_errors=True)
        with zipfile.ZipFile(z) as zf: zf.extractall(tmp)
        top = [os.path.join(tmp, d) for d in os.listdir(tmp)]
        shutil.move(top[0] if len(top) == 1 and os.path.isdir(top[0]) else tmp, dest)
        if not WIN:
            for f in glob.glob(f'{dest}/*'):
                if os.path.isfile(f): os.chmod(f, 0o755)
    return find_sdk()


# ---------------------------------------------------------------- the JDK (javac)
def find_jdk():
    cands = []
    if os.environ.get('JAVA_HOME'): cands.append(os.path.join(os.environ['JAVA_HOME'], 'bin'))
    w = shutil.which('javac')
    if w: cands.append(os.path.dirname(w))
    cands += glob.glob(f'{CACHE}/jdk*/bin') + glob.glob(f'{CACHE}/jdk*/Contents/Home/bin')
    for b in cands:
        if os.path.exists(os.path.join(b, 'javac' + EXE)) and os.path.exists(os.path.join(b, 'java' + EXE)): return b
    return None


def install_jdk():
    osn = 'windows' if WIN else 'mac' if sys.platform == 'darwin' else 'linux'
    arc = fetch(JDK_URL.format(os=osn), f'{CACHE}/temurin21-{osn}.' + ('zip' if WIN else 'tar.gz'), 'un JDK 21 (Eclipse Temurin, ~190 Mo)')
    if WIN:
        with zipfile.ZipFile(arc) as z: z.extractall(CACHE)
    else:
        with tarfile.open(arc) as t: t.extractall(CACHE)
    return find_jdk()


# ---------------------------------------------------------------- build
def run(cmd, **k):
    r = subprocess.run(cmd, capture_output=True, text=True, **k)
    if r.returncode: sys.exit(f"FAILED: {' '.join(map(str, cmd))[:300]}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r.stdout


def icons(res):
    from PIL import Image
    im = Image.open(f'{ROOT}/tools/win/icon.png').convert('RGBA')
    for d, s in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
        os.makedirs(f'{res}/mipmap-{d}', exist_ok=True); im.resize((s, s), Image.LANCZOS).save(f'{res}/mipmap-{d}/ic_launcher.png')


def main():
    accept = '--accept-license' in sys.argv
    ver = version(); code = int(round(float(re.sub(r'[^\d.]', '', ver) or 0) * 100)) or 1
    say(f'=== Retro Survivors {ver} — APK Android (versionCode {code}) ===')
    jdk = find_jdk() or (None if '--no-jdk-download' in sys.argv else install_jdk())
    if not jdk: sys.exit('javac not found: install a JDK 17 or newer (e.g. winget install EclipseAdoptium.Temurin.21.JDK)')
    java, javac, keytool = (os.path.join(jdk, n + EXE) for n in ('java', 'javac', 'keytool'))
    sdk = find_sdk() or install_sdk(accept)
    if not sdk: sys.exit('Android SDK build tools not found')
    bt, android_jar = sdk; say(f'JDK : {jdk}\nSDK : {bt} + {android_jar}')
    shutil.rmtree(WORK, ignore_errors=True); os.makedirs(f'{WORK}/classes'); os.makedirs(f'{WORK}/dex')
    # the manifest with the version, the icons, the resources
    man = open(f'{SRC}/AndroidManifest.xml', encoding='utf-8').read().replace('package="com.retrosurvivors.app"', f'package="com.retrosurvivors.app" android:versionCode="{code}" android:versionName="{ver}"')
    open(f'{WORK}/AndroidManifest.xml', 'w', encoding='utf-8').write(man)
    icons(f'{WORK}/res')
    say('Resources (aapt2)...')
    run([f'{bt}/aapt2{EXE}', 'compile', '--dir', f'{WORK}/res', '-o', f'{WORK}/res.zip'])
    run([f'{bt}/aapt2{EXE}', 'link', '-o', f'{WORK}/base.apk', '-I', android_jar, '--manifest', f'{WORK}/AndroidManifest.xml',
         '--min-sdk-version', '24', '--target-sdk-version', API, f'{WORK}/res.zip'])
    say('Code (javac + d8)...')
    run([javac, '-source', '11', '-target', '11', '-encoding', 'utf8', '-nowarn', '-Xlint:-options', '-classpath', android_jar, '-d', f'{WORK}/classes', f'{SRC}/MainActivity.java'])
    run([java, '-cp', f'{bt}/lib/d8.jar', 'com.android.tools.r8.D8', '--release', '--min-api', '24', '--lib', android_jar, '--output', f'{WORK}/dex']
        + glob.glob(f'{WORK}/classes/**/*.class', recursive=True))
    say('The game into the APK (~1 GB, a few minutes)...')
    raw = f'{WORK}/unaligned.apk'
    with zipfile.ZipFile(f'{WORK}/base.apk') as src, zipfile.ZipFile(raw, 'w', allowZip64=False) as z:
        for i in src.infolist(): z.writestr(i, src.read(i.filename))   # (resources.arsc stays stored, as Android 11+ wants)
        z.write(f'{WORK}/dex/classes.dex', 'classes.dex', zipfile.ZIP_DEFLATED)
        n = 0
        for p, rel in RL.game_files():
            z.write(p, 'assets/game/' + rel, zipfile.ZIP_STORED if os.path.splitext(p)[1].lower() in STORED else zipfile.ZIP_DEFLATED); n += 1
    say(f'  {n} game files')
    aligned = f'{WORK}/aligned.apk'
    run([f'{bt}/zipalign{EXE}', '-p', '-f', '4', raw, aligned])
    if not os.path.exists(KEY):
        os.makedirs(os.path.dirname(KEY), exist_ok=True)
        run([keytool, '-genkeypair', '-keystore', KEY, '-alias', KEY_ALIAS, '-keyalg', 'RSA', '-keysize', '2048', '-validity', '36500',
             '-dname', 'CN=Retro Survivors, O=Fan-made', '-storepass', KEY_PASS, '-keypass', KEY_PASS])
        say(f'Signing key created: {KEY}  (keep it: updates must be signed with the same key)')
    out = f'{ROOT}/dist/RetroSurvivors-{ver}.apk'
    say('Signing (apksigner)...')
    run([java, '-jar', f'{bt}/lib/apksigner.jar', 'sign', '--ks', KEY, '--ks-key-alias', KEY_ALIAS, '--ks-pass', f'pass:{KEY_PASS}', '--key-pass', f'pass:{KEY_PASS}',
         '--min-sdk-version', '24', '--out', out, aligned])
    run([java, '-jar', f'{bt}/lib/apksigner.jar', 'verify', '--min-sdk-version', '24', out])
    for f in (raw, aligned): os.remove(f)
    say(f'\nOK : {out} ({os.path.getsize(out) >> 20} MB)\nOn the phone: copy the file, then open it (allow installing unknown apps),'
        f'\nou : adb install -r "{out}"')


if __name__ == '__main__':
    main()
