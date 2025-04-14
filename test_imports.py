#!/usr/bin/env python3
"""Test script to verify imports are working."""

import sys
print(f"Python version: {sys.version}")

try:
    import PyPDF2
    print(f"PyPDF2 version: {getattr(PyPDF2, '__version__', 'unknown')}")
except ImportError as e:
    print(f"ERROR importing PyPDF2: {e}")

try:
    import pdf2image
    print(f"pdf2image imported successfully")
except ImportError as e:
    print(f"ERROR importing pdf2image: {e}")

try:
    import pytesseract
    print(f"pytesseract version: {getattr(pytesseract, '__version__', 'unknown')}")
except ImportError as e:
    print(f"ERROR importing pytesseract: {e}")

try:
    from PyQt6.QtWidgets import QApplication
    print("PyQt6 successfully imported")
except ImportError as e:
    print(f"ERROR importing PyQt6: {e}")

print("Import test completed") 