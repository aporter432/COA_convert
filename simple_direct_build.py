"""
Simple direct build script for COA Analyzer
Builds the executable without Poetry dependencies
"""

import os
import sys
import subprocess
import shutil

# Just install PyInstaller if needed
try:
    import PyInstaller
except ImportError:
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

# Get the script directory
current_dir = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("COA Analyzer Simple Build Script")
print("=" * 60)
print(f"Working from directory: {current_dir}")

# Clean previous builds
print("\nCleaning previous builds...")
# Clean PyInstaller build directories
if os.path.exists('dist'):
    print("Removing dist directory...")
    shutil.rmtree('dist')
if os.path.exists('build'):
    print("Removing build directory...")
    shutil.rmtree('build')

# Remove any .spec files created by PyInstaller
for file in os.listdir(current_dir):
    if file.endswith('.spec'):
        print(f"Removing spec file: {file}")
        os.remove(os.path.join(current_dir, file))

# Clean pycache directories which can cause issues
for root, dirs, files in os.walk(current_dir):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        print(f"Removing pycache: {pycache_path}")
        shutil.rmtree(pycache_path)

print("Cleanup complete!")

# Set the script path to the main file
script_path = os.path.join(current_dir, "coa_analyzer", "coa_analyzer.py")
print(f"Building from main script: {script_path}")

# Run PyInstaller
print("\nRunning PyInstaller...")
subprocess.run([
    sys.executable, 
    "-m", 
    "PyInstaller",
    "--onefile",       # Single executable
    "--windowed",      # No console window
    "--clean",         # Clean cache
    "--distpath", os.path.join(current_dir, "dist"),  # Explicitly set dist path
    "--workpath", os.path.join(current_dir, "build"), # Explicitly set build path
    "--specpath", current_dir,  # Explicitly set spec path
    "--name=COA_Analyzer",  # Output name
    script_path
], check=True)

print("\n" + "=" * 60)
print("Build completed!")
print(f"Executable is in: {os.path.join(current_dir, 'dist', 'COA_Analyzer.exe')}")
print("\nNext step: Open simple_installer_script.iss in Inno Setup and click Compile")
print("=" * 60)

input("\nPress Enter to exit...") 