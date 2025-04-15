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
; Tesseract installer
Source: "tesseract-ocr-w64-setup-v5.3.1.20230401.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install Tesseract OCR first if not already installed
Filename: "{tmp}\tesseract-ocr-w64-setup-v5.3.1.20230401.exe"; Parameters: "/S"; Check: not IsTesseractInstalled; StatusMsg: "Installing Tesseract OCR (required)..."
; Launch the app after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function IsTesseractInstalled: Boolean;
begin
  Result := DirExists('C:\Program Files\Tesseract-OCR') or DirExists('C:\Program Files (x86)\Tesseract-OCR');
end; 