"""Retro Survivors in the browser, from this folder: a local web server on 127.0.0.1 (the first free port from 8765),
no browser cache (always the files as they are now), then the default browser opens the game.
  python tools/serve_local.py [--no-browser] [port]      (or play_local.bat / play_local.sh at the repo's root)
Close the window (or Ctrl+C) to stop it."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import http.server, socket, sys, threading, webbrowser, functools


class NoCache(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.webp': 'image/webp', '.mp3': 'audio/mpeg',
                      '.json': 'application/json', '.js': 'text/javascript', '.woff2': 'font/woff2'}
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass


def free_port(start):
    for p in range(start, start + 40):
        with socket.socket() as s:
            try: s.bind(('127.0.0.1', p)); return p
            except OSError: continue
    sys.exit('no free port between %d and %d' % (start, start + 39))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    port = free_port(int(args[0]) if args else 8765)
    game = _os.path.join(ROOT, 'game')
    if not _os.path.exists(_os.path.join(game, 'index.html')): sys.exit('game/index.html not found')
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(NoCache, directory=game))
    url = f'http://127.0.0.1:{port}/'
    print(f'Retro Survivors: {url}\nKeep this window open while playing; close it (or press Ctrl+C) to stop the server.', flush=True)
    if '--no-browser' not in sys.argv: threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass


if __name__ == '__main__':
    main()
