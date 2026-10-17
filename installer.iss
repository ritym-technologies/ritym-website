; PulseStage MIDI Studio - Inno Setup 6 Script
; Generates standalone Windows setup executable: PulseStage-Setup-1.0.0-x64.exe

#define MyAppName "PulseStage"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "RiTym Technologies"
#define MyAppURL "https://ritym.com"
#define MyAppExeName "PulseStage.exe"
#define MyAppIcon "D:\Projects\MIDI\pulsestage.ico"
#define MyDistDir "D:\Projects\MIDI\dist\PulseStage"
#define MyOutputDir "D:\Projects\MIDI\dist"

[Setup]
AppId={{5E28A359-2E8F-4D88-B341-92A1A8EF90B1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL="https://ritym.com/pulsestage.html"
AppUpdatesURL="https://ritym.com/pulsestage.html"
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=D:\Projects\MIDI\LICENSE.txt
OutputDir={#MyOutputDir}
OutputBaseFilename=PulseStage-Setup-1.0.0-x64
SetupIconFile={#MyAppIcon}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequiredOverridesAllowed=dialog
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\Projects\MIDI\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\pulsestage.ico"
Name: "{group}\PulseStage User Guide"; Filename: "{app}\_internal\docs\PULSESTAGE-USER-GUIDE.html"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\pulsestage.ico"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
