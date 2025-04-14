# COA Analyzer Windows 10 Pro Package

This package contains everything needed to build and install the COA Analyzer on Windows 10 Pro systems.

## Contents

- `build.bat` - Automated build script
- `build_script.py` - Python build script
- `installer_script.iss` - Inno Setup installer script

## Installation Instructions

1. **Prerequisites**
   - Windows 10 Pro
   - Administrator privileges
   - Internet connection
   - 500MB free disk space

2. **Installation Steps**
   1. Right-click on `build.bat` and select "Run as administrator"
   2. Wait for the build process to complete (this may take several minutes)
   3. When complete, navigate to the `Output` directory
   4. Run `COA_Analyzer_Setup.exe` to install the application

3. **What the Installer Does**
   - Installs Python 3.8 or later
   - Installs Tesseract OCR
   - Installs Visual C++ Redistributable
   - Creates start menu shortcuts
   - Adds desktop shortcut (optional)

## Troubleshooting

If you encounter any issues during installation:

1. **Build Fails**
   - Ensure you're running as administrator
   - Check your internet connection
   - Verify you have enough disk space

2. **Installer Fails**
   - Check the log file in the `Output` directory
   - Try running the installer again
   - If problems persist, contact support

3. **Application Won't Start**
   - Check if Tesseract OCR is installed correctly
   - Verify Visual C++ Redistributable is installed
   - Try reinstalling the application

## Support

For additional help or to report issues:
- Check the main repository README
- Open an issue on GitHub
- Contact the development team 