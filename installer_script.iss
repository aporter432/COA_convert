#define MyAppName "COA Analyzer"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Your Company"
#define MyAppExeName "COA_Analyzer.exe"

[Setup]
AppId={{YOUR-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=COA_Analyzer_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
MinVersion=6.1.7601

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\COA_Analyzer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Code]
// Constants for download URLs
const
  VC_REDIST_URL = 'https://aka.ms/vs/17/release/vc_redist.x64.exe';
  TESSERACT_URL = 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe';
  PYTHON_URL = 'https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe';

// Check if Visual C++ Redistributable is installed
function IsVCRedistInstalled: Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Version', Version);
end;

// Check if Python is installed
function IsPythonInstalled: Boolean;
var
  PythonPath: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', PythonPath) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.8\InstallPath', '', PythonPath);
end;

// Check if Tesseract is installed
function IsTesseractInstalled: Boolean;
begin
  Result := DirExists('C:\Program Files\Tesseract-OCR') or DirExists('C:\Program Files (x86)\Tesseract-OCR');
end;

// Check available disk space (minimum 500MB required)
function HasEnoughDiskSpace: Boolean;
var
  RequiredSpace: Cardinal;
  AvailableSpace: Cardinal;
begin
  RequiredSpace := 500 * 1024 * 1024; // 500MB in bytes
  AvailableSpace := GetSpaceOnDisk(ExpandConstant('{app}'), False);
  Result := AvailableSpace >= RequiredSpace;
end;

// Check Windows version (Windows 7 SP1 or later required)
function IsWindowsVersionSupported: Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  Result := (Version.Major > 6) or 
            ((Version.Major = 6) and (Version.Minor >= 1) and (Version.ServicePackMajor >= 1));
end;

// Download and install a component
function DownloadAndInstall(URL: String; ComponentName: String): Boolean;
var
  ResultCode: Integer;
  DownloadPath: String;
begin
  DownloadPath := ExpandConstant('{tmp}\' + ExtractFileName(URL));
  
  if not DownloadTemporaryFile(URL, DownloadPath, '', @DownloadProgressCallback) then
  begin
    MsgBox('Failed to download ' + ComponentName + '. Please check your internet connection and try again.',
      mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  if not Exec(DownloadPath, '/quiet /norestart', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
  begin
    MsgBox('Failed to install ' + ComponentName + '. Error code: ' + IntToStr(ResultCode),
      mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  Result := True;
end;

// Initialize setup
function InitializeSetup(): Boolean;
var
  MissingComponents: String;
begin
  Result := True;
  MissingComponents := '';

  // Check Windows version
  if not IsWindowsVersionSupported then
  begin
    MsgBox('This application requires Windows 7 SP1 or later. Installation will now exit.',
      mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Check disk space
  if not HasEnoughDiskSpace then
  begin
    MsgBox('Insufficient disk space. Please free up at least 500MB of space and try again.',
      mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Check Visual C++ Redistributable
  if not IsVCRedistInstalled then
  begin
    if MsgBox('Visual C++ Redistributable is required. Would you like to install it now?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      if not DownloadAndInstall(VC_REDIST_URL, 'Visual C++ Redistributable') then
      begin
        Result := False;
        Exit;
      end;
    end
    else
    begin
      MissingComponents := MissingComponents + 'Visual C++ Redistributable' + #13#10;
    end;
  end;

  // Check Python
  if not IsPythonInstalled then
  begin
    if MsgBox('Python 3.8 or later is required. Would you like to install it now?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      if not DownloadAndInstall(PYTHON_URL, 'Python') then
      begin
        Result := False;
        Exit;
      end;
    end
    else
    begin
      MissingComponents := MissingComponents + 'Python 3.8 or later' + #13#10;
    end;
  end;

  // Check Tesseract
  if not IsTesseractInstalled then
  begin
    if MsgBox('Tesseract OCR is required. Would you like to install it now?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      if not DownloadAndInstall(TESSERACT_URL, 'Tesseract OCR') then
      begin
        Result := False;
        Exit;
      end;
    end
    else
    begin
      MissingComponents := MissingComponents + 'Tesseract OCR' + #13#10;
    end;
  end;

  // If any components are still missing, show error
  if MissingComponents <> '' then
  begin
    MsgBox('The following required components are missing:' + #13#10 + #13#10 +
      MissingComponents + #13#10 +
      'Please install these components and try again.',
      mbError, MB_OK);
    Result := False;
  end;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent 