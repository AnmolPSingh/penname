// Penname for macOS — a thin native shell around the Penname web app.
// No plugins, no IPC surface, no network: the whole product is the bundled
// web app, exactly as on iOS.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::webview::{DownloadEvent, WebviewWindowBuilder};

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // The window is declared in tauri.conf.json ("create": false) and
            // built here so a download handler can be attached. Without one
            // the web view cancels every download, and "Save key file" would
            // silently do nothing.
            let config = app
                .config()
                .app
                .windows
                .first()
                .cloned()
                .expect("tauri.conf.json declares the main window");
            WebviewWindowBuilder::from_config(app, &config)?
                .on_download(|_webview, event| match event {
                    // Only files the app itself generates (blob: URLs) may be
                    // saved. The destination is the user's Downloads folder,
                    // with " (1)" appended rather than overwriting — the
                    // sandbox grants exactly that folder.
                    DownloadEvent::Requested { url, .. } => url.scheme() == "blob",
                    _ => true,
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Penname");
}
