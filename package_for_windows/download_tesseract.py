"""
Download Tesseract OCR Installer
This script downloads the Tesseract OCR installer needed for the COA Analyzer
"""

import os
import sys
import urllib.request
import time

# URL for Tesseract OCR installer
TESSERACT_URL = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-v5.3.1.20230401.exe"
TESSERACT_INSTALLER = "tesseract-ocr-w64-setup-v5.3.1.20230401.exe"

def download_with_progress(url, filename):
    """Download a file with a progress bar"""
    print(f"Downloading {filename}...")
    
    def show_progress(count, block_size, total_size):
        percent = min(100, count * block_size * 100 / total_size)
        bar_length = 50
        filled_length = int(bar_length * percent / 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        # Clear line and redraw
        sys.stdout.write(f"\r|{bar}| {percent:.1f}% ")
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, show_progress)
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"\nError downloading {filename}: {e}")
        return False

def main():
    """Main function to download Tesseract OCR"""
    print("Preparing to download Tesseract OCR installer")
    print("This is required for the COA Analyzer to process PDF files")
    print("File size: approximately 35 MB")
    print()
    
    if os.path.exists(TESSERACT_INSTALLER):
        print(f"{TESSERACT_INSTALLER} already exists.")
        choice = input("Download again? (y/n): ").lower()
        if choice != 'y':
            print("Using existing file.")
            return
    
    success = download_with_progress(TESSERACT_URL, TESSERACT_INSTALLER)
    
    if success:
        print("\nThe Tesseract installer has been downloaded successfully.")
        print("You can now build the COA Analyzer.")
    else:
        print("\nThere was a problem downloading Tesseract.")
        print("Please try again or download it manually from:")
        print(TESSERACT_URL)
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main() 