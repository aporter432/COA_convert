import PyInstaller.__main__
import os
import sys
import shutil

def build_exe():
    # Clean previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # Create the executable
    PyInstaller.__main__.run([
        'coa_analyzer/coa_analyzer.py',
        '--onefile',
        '--windowed',
        '--name=COA_Analyzer',
        '--add-data=README.md:.',
        '--icon=output_images/output-1.png',
        '--clean',
        # Add hidden imports for PyQt6
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        # Add Tesseract data files
        '--add-binary=C:\\Program Files\\Tesseract-OCR\\tessdata:tessdata',
    ])

    # Create requirements.txt for documentation
    os.system('poetry export -f requirements.txt --output requirements.txt --without-hashes')

if __name__ == '__main__':
    build_exe() 