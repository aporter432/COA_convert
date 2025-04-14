@echo off
echo Building COA Analyzer...

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Install dependencies
poetry install

REM Build the executable
poetry run python build_script.py

REM Check if Inno Setup is installed
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo Inno Setup not found at %INNO_PATH%
    echo Please install Inno Setup from https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM Compile the installer
"%INNO_PATH%" installer_script.iss

echo Build complete!
echo The installer can be found in the Output directory.
pause 