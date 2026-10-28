"""Headless browser smoke test: serve the game dir, load the page, run scripted actions, capture screenshots + console.
env: VW, VH (viewport), DPR, MOBILE=1 (touch + mobile UA), PORT. Script globals: pg, out, time, shot(name), url(params)."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, time, json, threading, http.server, socketserver, functools
from playwright.sync_api import sync_playwright

ROOT = os.environ.get('ROOT', f'{ROOT}/game')
PORT = int(os.environ.get('PORT', '0'))   # (0.94: a free port unless PORT is given — 8765 is the: never take it)


class Q(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'   # (0.94: kept-alive connections, as stress.py: one socket per file ran Windows out of them, ERR_NO_BUFFER_SPACE)
    def log_message(self, *a): pass
    def handle(self):
        try: super().handle()
        except Exception: pass   # (a page closed mid-file: not a test failure)


def serve():
    handler = functools.partial(Q, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True); t.start()
    return httpd


def run(script, out=f'{ROOT}/tests/shots', w=None, h=None, query=''):
    os.makedirs(out, exist_ok=True)
    w = w or int(os.environ.get('VW', '1280')); h = h or int(os.environ.get('VH', '720'))
    dpr = float(os.environ.get('DPR', '1')); mobile = os.environ.get('MOBILE') == '1'
    httpd = serve(); port = httpd.server_address[1]
    logs = []
    try:
        with sync_playwright() as p:
            exe = os.environ.get('CHROME') or next((c for c in ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome'] if os.path.exists(c)), None)   # (0.50: the cloud machines' Chromium)
            b = p.chromium.launch(executable_path=exe, args=['--autoplay-policy=no-user-gesture-required', '--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
            ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, is_mobile=mobile, has_touch=mobile)
            pg = ctx.new_page()
            pg.on('console', lambda m: logs.append(f'[{m.type}] {m.text}'))
            pg.on('pageerror', lambda e: logs.append(f'[pageerror] {e}'))
            url = lambda q='': pg.goto(f'http://127.0.0.1:{port}/index.html' + (('?' + q) if q else ''))
            env = dict(pg=pg, out=out, time=time, url=url, logs=logs, PORT=port, shot=lambda n, **k: pg.screenshot(path=f'{out}/{n}.png', **k))
            exec(script, env)
            b.close()
    finally:
        httpd.shutdown()
    return logs


if __name__ == '__main__':
    script = open(sys.argv[1]).read()
    out = sys.argv[2] if len(sys.argv) > 2 else f'{ROOT}/tests/shots'
    logs = run(script, out)
    print('\n'.join(logs[-80:]))
