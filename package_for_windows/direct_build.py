"""
Direct build script for COA Analyzer
This script builds the application using PyInstaller directly, without Poetry
"""

import os
import sys
import subprocess
import shutil

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def install_dependencies():
    """Install only the required dependencies directly with pip"""
    print("\nInstalling required dependencies...")
    
    # Core dependencies needed for the application
    required_packages = [
        "PyPDF2>=3.0.1",
        "pdf2image>=1.16.3",
        "pytesseract>=0.3.10",
        "Pillow>=10.2.0",
        "PyQt6>=6.9.0",
        "psutil>=5.9.8",
        "pyinstaller"
    ]
    
    try:
        # Install dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--upgrade"
        ] + required_packages, check=True)
        
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def download_tesseract():
    """Check if Tesseract installer exists, download if not"""
    print("\nChecking for Tesseract installer...")
    
    tesseract_installer = os.path.join(SCRIPT_DIR, "tesseract-ocr-w64-setup-v5.3.1.20230401.exe")
    
    if os.path.exists(tesseract_installer):
        print(f"✓ Tesseract installer found: {tesseract_installer}")
        return True
    
    print("Tesseract installer not found. Running download script...")
    try:
        download_script = os.path.join(SCRIPT_DIR, "download_tesseract.py")
        subprocess.run([sys.executable, download_script], check=True)
        
        if os.path.exists(tesseract_installer):
            print("✓ Tesseract installer downloaded successfully")
            return True
        else:
            print("❌ Tesseract installer download failed")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download Tesseract: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller directly"""
    print("\nBuilding executable...")
    
    try:
        # Change to script directory
        os.chdir(SCRIPT_DIR)
        
        # Clean previous builds
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        if os.path.exists('build'):
            shutil.rmtree('build')
            
        # Main script to build
        script_path = os.path.join(SCRIPT_DIR, "coa_analyzer", "coa_analyzer.py")
        
        # Run PyInstaller
        subprocess.run([
            sys.executable, 
            "-m", 
            "PyInstaller",
            "--onefile",  # Create a single file
            "--windowed",  # Don't show console
            "--clean",  # Clean PyInstaller cache
            "--name=COA_Analyzer",  # Output name
            script_path
        ], check=True)
        
        print("✓ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def main():
    """Main function to build the application"""
    print("=" * 50)
    print("COA Analyzer Direct Build Script")
    print("=" * 50)
    print(f"Script directory: {SCRIPT_DIR}")
    
    # 1. Install dependencies
    if not install_dependencies():
        input("\nPress Enter to exit...")
        return
    
    # 2. Download Tesseract if needed
    if not download_tesseract():
        input("\nPress Enter to exit...")
        return
    
    # 3. Build the executable
    if not build_executable():
        input("\nPress Enter to exit...")
        return
    
    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print(f"Executable is in: {os.path.join(SCRIPT_DIR, 'dist', 'COA_Analyzer.exe')}")
    print("\nNext steps:")
    print("1. Install Inno Setup")
    print("2. Open simple_installer_script.iss in Inno Setup")
    print("3. Click Compile to create the installer")
    print("=" * 50)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main() 