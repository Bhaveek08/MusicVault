#define MyAppName "MusicVault"
#define MyAppVersion "2.0.4"
#define MyAppPublisher "MusicVault Project"
#define MyAppExeName "MusicVault.exe"

[Setup]
AppId={{D7D32FC1-10F0-4C0B-AE1C-1C5C17EB315A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\MusicVault
DefaultGroupName=MusicVault
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputBaseFilename=MusicVault-Setup
SetupIconFile=..\assets\musicvault.ico
UninstallDisplayIcon={app}\MusicVault.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
Uninstallable=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\MusicVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\MusicVault"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\MusicVault"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch MusicVault"; Flags: postinstall nowait skipifsilent unchecked

; User preferences/logs and the user's Music\MusicVault library are deliberately
; kept outside {app}; uninstall removes only installed application files.
