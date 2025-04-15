#define MyAppName "COA Analyzer"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "COA_Analyzer.exe"

[Setup]
AppId={{94A9D9F9-8E7E-4BE8-8307-C85D3E8F0BAF}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=COA_Analyzer_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application
Source: "dist\COA_Analyzer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Messages]
; Add a custom message about Tesseract
FinishedLabel=Setup has finished installing [name] on your computer.%n%nIMPORTANT: You need to install Tesseract OCR for this application to work.%n%nDownload from: https://github.com/UB-Mannheim/tesseract/wiki 