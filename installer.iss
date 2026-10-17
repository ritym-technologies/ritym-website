; PulseStage desktop: embedded Qt renderer and Python runtime included.
#define MyAppVersion "1.1.0"
#define MyRoot SourcePath
[Setup]
AppId={{5E28A359-2E8F-4D88-B341-92A1A8EF90B1}
AppName=PulseStage
AppVersion={#MyAppVersion}
AppPublisher=PulseStage
DefaultDirName={autopf}\PulseStage
DefaultGroupName=PulseStage
LicenseFile={#MyRoot}\LICENSE.txt
OutputDir={#MyRoot}\dist
OutputBaseFilename=PulseStage-Setup-{#MyAppVersion}-x64
SetupIconFile={#MyRoot}\pulsestage.ico
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\PulseStage.exe
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
[Files]
Source: "{#MyRoot}\dist\PulseStage\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyRoot}\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\PulseStage"; Filename: "{app}\PulseStage.exe"
Name: "{group}\Uninstall PulseStage"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PulseStage"; Filename: "{app}\PulseStage.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\PulseStage.exe"; Description: "Launch PulseStage"; Flags: nowait postinstall skipifsilent
