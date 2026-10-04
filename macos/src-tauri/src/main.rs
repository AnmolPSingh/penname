// Penname for macOS — a thin native shell around the Penname web app.
// No plugins, no IPC surface, no network: the whole product is the bundled
// web app, exactly as on iOS.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Penname");
}
