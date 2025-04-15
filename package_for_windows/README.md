# COA Analyzer - Windows Build & Deployment

This package contains everything needed to build and deploy the COA Analyzer application for Windows.

## Step 1: Build on your Windows PC

1. **Extract this zip file** to a folder on your Windows PC
2. **Run direct_build.py** to build the application
   ```
   python direct_build.py
   ```
   This script will:
   - Install all required dependencies
   - Download the Tesseract OCR installer if needed
   - Build the executable

3. **Run Inno Setup** to create the installer:
   - Download and install [Inno Setup](https://jrsoftware.org/isdl.php)
   - Open simple_installer_script.iss in Inno Setup
   - Click Compile to create the installer

## Step 2: Share with your friend

1. The final installer will be created in the Output folder as **COA_Analyzer_Setup.exe**
2. Send your friend:
   - COA_Analyzer_Setup.exe (you will need to zip it for email)
   - friend_instructions.txt

## Important Notes

- Email security may block .exe files. Zip the setup file before emailing it.
- Your friend needs admin rights to install the application.
- The installer will automatically install Tesseract OCR if needed.
- The application requires about 200MB of disk space when installed.

## Troubleshooting

- If you see any errors about missing packages, run:
  ```
  pip install PyPDF2 pdf2image pytesseract Pillow PyQt6 psutil pyinstaller
  ```
- If PyInstaller fails with path errors, try running the build script from the same folder it's located in
- Be sure Tesseract OCR installer is in the same folder as your simple_installer_script.iss when compiling with Inno Setup 