import PyInstaller.__main__
import os
import sys
import shutil
import glob

def clean_logs():
    """Clean up log files after successful run"""
    log_patterns = [
        '*.log',
        'build/*.log',
        'dist/*.log',
        '*.tmp',
        'build/*.tmp',
        'dist/*.tmp'
    ]
    
    for pattern in log_patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"Cleaned up: {file}")
            except Exception as e:
                print(f"Warning: Could not clean up {file}: {str(e)}")

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

    # Clean up logs after successful build
    clean_logs()

if __name__ == '__main__':
    try:
        build_exe()
        print("Build completed successfully!")
    except Exception as e:
        print(f"Build failed: {str(e)}")
        # Don't clean logs if build failed
        sys.exit(1) 