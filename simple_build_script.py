"""
Simple build script for COA Analyzer
This script creates a standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess

def clean_previous_builds():
    """Remove previous build artifacts"""
    print("Cleaning previous builds...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    print("Clean complete!")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    try:
        # Create the executable with PyInstaller
        command = [
            sys.executable, 
            '-m', 
            'PyInstaller',
            '--onefile',  # Create a single executable file
            '--windowed',  # Don't show console window
            '--clean',  # Clean PyInstaller cache
            '--name=COA_Analyzer',  # Name of the output executable
            'coa_analyzer/coa_analyzer.py'  # Script to build
        ]
        
        subprocess.run(command, check=True)
        print("Build successful! Executable is in the 'dist' folder.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main function to build the executable"""
    # Check if PyInstaller is installed
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'pyinstaller'], 
                      check=True, 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing PyInstaller: {e}")
            sys.exit(1)
    
    # Build the executable
    clean_previous_builds()
    build_executable()
    
    print("\nBuild process completed!")
    print("You can find the executable at: dist/COA_Analyzer.exe")
    print("Remember that users will need Tesseract OCR installed to use the application.")

if __name__ == "__main__":
    main() 