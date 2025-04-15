# COA Analyzer - Windows Build Guide

This guide will help you create a standalone Windows executable (.exe) from the COA Analyzer source code.

## Prerequisites

1. **Python 3.9 or later**
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure you check "Add Python to PATH" during installation

2. **Tesseract OCR**
   - Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to the default location (C:\Program Files\Tesseract-OCR)
   - Add Tesseract to your PATH environment variable

3. **Poetry (Python package manager)**
   - Open PowerShell or Command Prompt as administrator
   - Run: `pip install poetry`

4. **Visual C++ Redistributable**
   - Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Install the package

## Building the Executable

1. **Extract the zip file** to a folder of your choice

2. **Open Command Prompt** as administrator and navigate to the extracted folder:
   ```
   cd path\to\extracted\folder
   ```

3. **Install the project dependencies** using Poetry:
   ```
   poetry install
   ```

4. **Build the executable** using PyInstaller:
   ```
   poetry run python -m PyInstaller --onefile --windowed --name=COA_Analyzer --clean coa_analyzer/coa_analyzer.py
   ```

5. **Find the executable** in the `dist` folder

## Troubleshooting

- **Missing dependencies**: If you see errors about missing dependencies, run:
  ```
  poetry update
  ```

- **Tesseract not found**: Make sure Tesseract is installed and in your PATH. You can check by running:
  ```
  where tesseract
  ```

- **PyInstaller errors**: Make sure you're using the latest version:
  ```
  poetry add pyinstaller@latest
  ```

## Sharing the Application

The executable file (`COA_Analyzer.exe`) in the `dist` folder is a standalone application that can be shared with others. They will need:

1. Tesseract OCR installed on their system
2. Visual C++ Redistributable installed

For a more professional distribution, consider using Inno Setup to create an installer that includes these dependencies.

## Running the Application

Simply double-click the `COA_Analyzer.exe` file to run the application. You can also create a shortcut on your desktop for easier access. 