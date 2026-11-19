import SwiftUI
import WebKit
import UIKit

@main
struct MusicVaultApp: App {
    var body: some Scene {
        WindowGroup {
            MusicVaultView()
                .preferredColorScheme(.dark)
                .ignoresSafeArea()
        }
    }
}

struct MusicVaultView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = false

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 8/255, green: 9/255, blue: 11/255, alpha: 1)
        webView.scrollView.backgroundColor = webView.backgroundColor
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.navigationDelegate = context.coordinator

        guard let page = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "shared") else {
            let html = "<html><body style='background:#08090b;color:white;font-family:-apple-system;padding:32px'>MusicVault UI assets are missing from this build.</body></html>"
            webView.loadHTMLString(html, baseURL: nil)
            return webView
        }
        let readAccess = page.deletingLastPathComponent()
        webView.loadFileURL(page, allowingReadAccessTo: readAccess)
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }
            if url.isFileURL {
                decisionHandler(.allow)
                return
            }
            decisionHandler(.cancel)
        }
    }
}
