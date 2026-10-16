// Penname for macOS — a thin native shell around the Penname web app.
// No plugins and no network: the whole product is the bundled web app,
// exactly as on iOS. The shell adds two things the sandboxed web view cannot
// do itself: a Save dialog, and opening philanthropel.com in the browser.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::webview::WebviewWindowBuilder;

const WEBSITE: &str = "https://philanthropel.com/";

/// Ask where to keep a file the app produced, then write it there. Resolves
/// to false when the user cancels. The Save dialog is what grants the sandbox
/// access to the chosen location, so no folder entitlement is needed.
#[tauri::command]
async fn save_file(name: String, bytes: Vec<u8>) -> Result<bool, String> {
    let Some(file) = rfd::AsyncFileDialog::new().set_file_name(&name).save_file().await else {
        return Ok(false);
    };
    std::fs::write(file.path(), bytes).map_err(|e| e.to_string())?;
    Ok(true)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![save_file])
        .setup(|app| {
            // The window is declared in tauri.conf.json ("create": false) and
            // built here so a navigation handler can be attached.
            let config = app
                .config()
                .app
                .windows
                .first()
                .cloned()
                .expect("tauri.conf.json declares the main window");
            WebviewWindowBuilder::from_config(app, &config)?
                .on_navigation(|url| {
                    // The web view only ever shows the bundled app. Links to
                    // our own website open in the default browser; anything
                    // else goes nowhere.
                    if url.scheme() == "tauri" {
                        return true;
                    }
                    if url.as_str().starts_with(WEBSITE) {
                        let _ = std::process::Command::new("/usr/bin/open").arg(url.as_str()).spawn();
                    }
                    false
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Penname");
}
