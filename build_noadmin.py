"""
Build script for creating a non-admin COA Analyzer executable and installer
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
    if os.path.exists('Output'):
        shutil.rmtree('Output')
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            os.remove(file)
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

def build_noadmin_installer():
    """Build the non-admin installer using InnoSetup"""
    print("Building non-admin installer...")
    try:
        # Find Inno Setup compiler
        inno_setup_compiler = r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
        if not os.path.exists(inno_setup_compiler):
            inno_setup_compiler = r'C:\Program Files\Inno Setup 6\ISCC.exe'
            if not os.path.exists(inno_setup_compiler):
                print("Error: Inno Setup compiler not found. Please install Inno Setup 6.")
                return
        
        # Run Inno Setup compiler
        command = [
            inno_setup_compiler,
            'simple_installer_script.iss'
        ]
        
        subprocess.run(command, check=True)
        print("Installer build successful! Setup file is in the 'Output' folder.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building installer: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    """Main function to build the executable and installer"""
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
    
    # Clean up previous builds
    clean_previous_builds()
    
    # Build the executable
    build_executable()
    
    # Build the non-admin installer
    build_noadmin_installer()
    
    print("\nBuild process completed!")
    print("You can find the executable at: dist/COA_Analyzer.exe")
    print("You can find the installer at: Output/COA_Analyzer_Setup_NoAdmin.exe")
    print("\nIMPORTANT: This installer will not require admin rights and will install")
    print("to the user's AppData folder instead of Program Files.")

if __name__ == "__main__":
    main() 