#define MyAppName "COA Analyzer"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "COA_Analyzer.exe"

[Setup]
AppId={{94A9D9F9-8E7E-4BE8-8307-C85D3E8F0BAF}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Change default install location to user's AppData folder (doesn't require admin rights)
DefaultDirName={userappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=COA_Analyzer_Setup_NoAdmin
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Set privileges to lowest to avoid requiring admin rights
PrivilegesRequired=lowest
; Disable auto-running with privileges as we don't want to try to elevate
PrivilegesRequiredOverridesAllowed=dialog
; Disable creating a Program Files folder since we're installing in user's directory
DisableProgramGroupPage=yes
; Set application directory as current directory
SetupLogging=yes
; Don't create uninstall registry entries in HKLM (requires admin)
CreateUninstallRegKey=no
UninstallDisplayIcon={app}\{#MyAppExeName}
AlwaysShowDirOnReadyPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application
Source: "dist\COA_Analyzer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Create a start menu shortcut in user's start menu, not all users
Name: "{userstartmenu}\Programs\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
; Launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Messages]
; Add a custom message about Tesseract
FinishedLabel=Setup has finished installing [name] on your computer.%n%nIMPORTANT: You need to install Tesseract OCR for this application to work.%n%nDownload from: https://github.com/UB-Mannheim/tesseract/wiki 