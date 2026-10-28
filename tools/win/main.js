// Electron shell of the Windows build (make_exe.bat): the game is served from resources/app/game through the
// 'rs://' protocol, so fetch() of the JSON / sounds works like on a web server and the saves (localStorage) persist.
const { app, BrowserWindow, protocol, net, Menu, shell } = require('electron');
const path = require('path');
const { pathToFileURL } = require('url');
app.setName('Retro Survivors');
protocol.registerSchemesAsPrivileged([{ scheme: 'rs', privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true, corsEnabled: true } }]);
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
app.commandLine.appendSwitch('enable-gpu-rasterization');
// 0.44 (weak PCs): the GPU even when Chromium's blocklist would fall back to a (much slower) software canvas, and the
// dedicated GPU on laptops that have two
app.commandLine.appendSwitch('ignore-gpu-blocklist');
app.commandLine.appendSwitch('force_high_performance_gpu');
app.whenReady().then(() => {
  const root = path.join(__dirname, 'game');
  protocol.handle('rs', (req) => {
    let p = decodeURIComponent(new URL(req.url).pathname);
    if (!p || p === '/') p = '/index.html';
    const fp = path.join(root, path.normalize(p));
    if (!fp.startsWith(root)) return new Response('forbidden', { status: 403 });
    return net.fetch(pathToFileURL(fp).toString());
  });
  Menu.setApplicationMenu(null);
  const win = new BrowserWindow({
    width: 1600, height: 900, minWidth: 800, minHeight: 450, backgroundColor: '#120d08', title: 'Retro Survivors',
    icon: path.join(__dirname, 'icon.png'), autoHideMenuBar: true, show: false,
    webPreferences: { contextIsolation: true, backgroundThrottling: false },
  });
  win.once('ready-to-show', () => { win.maximize(); win.show(); });
  win.loadURL('rs://game/index.html');
  win.webContents.on('before-input-event', (e, input) => {   // F11 = full screen
    if (input.type === 'keyDown' && input.key === 'F11') { win.setFullScreen(!win.isFullScreen()); e.preventDefault(); }
  });
  // (0.91: a web link — the Discord in the credits and after Goultard — opens in the system browser, nothing else opens)
  win.webContents.setWindowOpenHandler(({ url }) => { if (/^https:\/\//.test(url)) shell.openExternal(url); return { action: 'deny' }; });
});
app.on('window-all-closed', () => app.quit());
