package com.musicvault.mobile;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.webkit.WebChromeClient;
import androidx.webkit.WebViewAssetLoader;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public final class MainActivity extends Activity {
    private static final String SMOKE_TEST_TAG = "MusicVaultSmokeTest";
    private static final String APP_ASSET_URL = "https://appassets.androidplatform.net/assets/index.html";
    private static final Set<String> SPOTIFY_HOSTS = new HashSet<>(Arrays.asList(
        "open.spotify.com", "www.spotify.com", "spotify.com", "spotify.link"
    ));

    private WebView webView;
    private WebViewAssetLoader assetLoader;

    static boolean isAllowedSpotifyUri(Uri uri) {
        if (uri == null || !"https".equalsIgnoreCase(uri.getScheme())) return false;
        String host = uri.getHost();
        if (host == null) return false;
        host = host.toLowerCase(Locale.ROOT);
        return SPOTIFY_HOSTS.contains(host) && (uri.getPort() == -1 || uri.getPort() == 443)
            && uri.getUserInfo() == null;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(8, 9, 11));
        getWindow().setNavigationBarColor(Color.rgb(8, 9, 11));
        getWindow().getDecorView().setSystemUiVisibility(0);

        assetLoader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .build();

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(8, 9, 11));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportMultipleWindows(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public android.webkit.WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (!APP_ASSET_URL.equals(url)) return;

                // A foreground Activity is not proof that the WebView screen rendered.
                // Check the shared app bootstrap, expected controls and theme before
                // declaring the Android UI ready to the emulator smoke test.
                String readinessCheck =
                    "(function(){return Boolean(" +
                    "document.documentElement.dataset.musicvaultReady === 'true' && " +
                    "document.getElementById('youtubeTab') && " +
                    "document.getElementById('spotifyTab') && " +
                    "document.getElementById('queueList') && " +
                    "getComputedStyle(document.body).backgroundColor === 'rgb(8, 9, 11)'" +
                    ");})()";
                view.evaluateJavascript(readinessCheck, result -> {
                    if ("true".equals(result)) {
                        Log.i(SMOKE_TEST_TAG, "UI_READY");
                    } else {
                        Log.e(SMOKE_TEST_TAG, "UI_NOT_READY result=" + result);
                    }
                });
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        android.webkit.WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request.isForMainFrame()) {
                    Log.e(SMOKE_TEST_TAG, "MAIN_FRAME_LOAD_FAILED: " + error.getDescription());
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equalsIgnoreCase(uri.getScheme())
                    && "appassets.androidplatform.net".equalsIgnoreCase(uri.getHost())
                    && uri.getPath() != null && uri.getPath().startsWith("/assets/")) return false;
                if (isAllowedSpotifyUri(uri)) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                        startActivity(intent);
                    } catch (ActivityNotFoundException ignored) {
                        Toast.makeText(MainActivity.this, "Install Spotify or open this link in a browser.", Toast.LENGTH_LONG).show();
                    }
                }
                return true;
            }

        });
        setContentView(webView);
        webView.loadUrl(APP_ASSET_URL);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
