; Inno Setup script for Time Tracker
; Requires PyInstaller output in installer_files_{version}/TimeTracker/

#define MyAppName "Time Tracker"
#define MyAppExeName "TimeTracker.exe"
#define MyAppPublisher "Amir Labai"
#define MyAppURL "https://github.com/Amirlabai/time_logger/releases/latest"
#define MyAppUpdatesURL "https://github.com/Amirlabai/time_logger/releases/latest"

[Setup]
AppId={{C8E4F2A1-9B3D-4E56-8F10-2D7C9E5A1B04}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppUpdatesURL}
DefaultDirName={autopf}\TimeTracker
DefaultGroupName={#MyAppName}
OutputDir=installers
OutputBaseFilename=TimeTracker_Setup_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=lib\icons\timer_icon_32.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\installer_files_{#MyAppVersion}\TimeTracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
