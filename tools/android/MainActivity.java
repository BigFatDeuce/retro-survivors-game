// 0.94 (owner: an APK like the other builds): the whole Android app — one full-screen WebView showing the game's own
// files from the APK's assets (assets/game/…), served at https://appassets.androidplatform.net/ (a real https origin:
// fetch, createImageBitmap, WebGL, Web Audio and localStorage work as on the web; the saves stay in the app's data).
// Built without Gradle nor any library by tools/make_apk.py (javac + d8 + aapt2 + apksigner of the Android SDK).
package com.retrosurvivors.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Message;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

public class MainActivity extends Activity {
    static final String HOST = "appassets.androidplatform.net";
    static final Map<String, String> MIME = new HashMap<>();
    static {
        String[][] m = { { "html", "text/html" }, { "js", "text/javascript" }, { "css", "text/css" }, { "json", "application/json" },
            { "webp", "image/webp" }, { "png", "image/png" }, { "jpg", "image/jpeg" }, { "svg", "image/svg+xml" }, { "ico", "image/x-icon" },
            { "mp3", "audio/mpeg" }, { "ogg", "audio/ogg" }, { "wav", "audio/wav" }, { "woff2", "font/woff2" }, { "woff", "font/woff" }, { "ttf", "font/ttf" }, { "txt", "text/plain" } };
        for (String[] p : m) MIME.put(p[0], p[1]);
    }
    WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON | WindowManager.LayoutParams.FLAG_FULLSCREEN);
        if (Build.VERSION.SDK_INT >= 28) getWindow().getAttributes().layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setSupportMultipleWindows(true);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        s.setTextZoom(100);   // (the phone's font size setting must not resize the game's texts)
        web.addJavascriptInterface(new Bridge(), "RSAndroid");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) { return asset(r.getUrl()); }
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                if (HOST.equals(r.getUrl().getHost())) return false;
                open(r.getUrl()); return true;   // (the Discord link, the credits' links: in the phone's browser)
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onCreateWindow(WebView v, boolean dialog, boolean user, Message msg) {   // (window.open: the browser too)
                WebView t = new WebView(MainActivity.this);
                t.setWebViewClient(new WebViewClient() {
                    @Override
                    public boolean shouldOverrideUrlLoading(WebView w, WebResourceRequest r) { open(r.getUrl()); return true; }
                });
                ((WebView.WebViewTransport) msg.obj).setWebView(t); msg.sendToTarget(); return true;
            }
        });
        setContentView(web);
        immersive();
        web.loadUrl("https://" + HOST + "/index.html");
    }

    // a file of the game, from the APK's assets (the ?v= of the URLs is not part of the path)
    WebResourceResponse asset(Uri u) {
        if (!HOST.equals(u.getHost())) return null;
        String p = u.getPath(); if (p == null || p.equals("/")) p = "/index.html";
        Map<String, String> h = new HashMap<>();
        h.put("Access-Control-Allow-Origin", "*");
        h.put("Cache-Control", "no-cache");
        try {
            InputStream in = getAssets().open("game" + p);
            String ext = p.substring(p.lastIndexOf('.') + 1).toLowerCase();
            String mime = MIME.containsKey(ext) ? MIME.get(ext) : "application/octet-stream";
            return new WebResourceResponse(mime, mime.startsWith("text/") || mime.endsWith("json") ? "utf-8" : null, 200, "OK", h, in);
        } catch (Exception e) {
            return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", h, new ByteArrayInputStream(new byte[0]));
        }
    }

    void open(Uri u) {
        try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception e) { }
    }

    void immersive() {
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    @Override
    public void onWindowFocusChanged(boolean f) { super.onWindowFocusChanged(f); if (f) immersive(); }

    // the phone's Back key = Escape in the game (pause, close a window, back to the previous menu); it never closes the app
    @Override
    public boolean onKeyDown(int code, KeyEvent e) {
        if (code == KeyEvent.KEYCODE_BACK) {
            web.evaluateJavascript("(()=>{const o={key:'Escape',code:'Escape',bubbles:true};window.dispatchEvent(new KeyboardEvent('keydown',o));window.dispatchEvent(new KeyboardEvent('keyup',o));})()", null);
            return true;
        }
        return super.onKeyDown(code, e);
    }

    // in the background: the run paused, the sounds stopped (the game's own pause on a hidden page, Audio2)
    @Override
    protected void onPause() {
        web.evaluateJavascript("(()=>{try{if(window.Game&&Game.autoPause)Game.autoPause();if(window.Audio2){if(Audio2.ctx)Audio2.ctx.suspend();if(Audio2.music)Audio2.music.pause();}}catch(e){}})()", null);
        web.onPause(); super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume(); web.onResume(); immersive();
        web.evaluateJavascript("(()=>{try{if(window.Audio2)Audio2.resume();}catch(e){}})()", null);
    }

    // the game's 'Quitter' button (UI.quitGame) closes the app
    class Bridge {
        @JavascriptInterface
        public void quit() { runOnUiThread(() -> finishAndRemoveTask()); }
    }
}
