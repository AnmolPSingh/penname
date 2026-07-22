; Inno Setup script — builds Penname-Setup.exe (a native Windows installer)
; from the PyInstaller one-folder build in dist\Penname.
;
;   iscc /DAppVersion=v2.0.1 packaging\penname.iss
;
; Installs per-user (no admin / UAC prompt needed), adds Start-menu and optional
; desktop shortcuts. Unsigned — SmartScreen shows a one-time prompt; the README
; install guide covers it.

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif

[Setup]
AppName=Penname
AppVersion={#AppVersion}
AppPublisher=Philanthropel Limited
AppPublisherURL=https://github.com/AnmolPSingh/penname
SourceDir=..
OutputDir=dist
OutputBaseFilename=Penname-Setup
DefaultDirName={autopf}\Penname
DefaultGroupName=Penname
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\Penname\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Penname"; Filename: "{app}\Penname.exe"
Name: "{group}\Uninstall Penname"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Penname"; Filename: "{app}\Penname.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Penname.exe"; Description: "Launch Penname"; Flags: nowait postinstall skipifsilent
