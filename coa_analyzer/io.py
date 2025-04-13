"""Input/output operations for COA Analyzer."""

import csv
import os
import sys
from typing import Dict, List

from .core import TestResult


def read_pdf_file(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        # Only import PyPDF2 when needed
        from PyPDF2 import PdfReader
    except ImportError:
        print("Error: PyPDF2 library is required for PDF support.")
        print("Install it using: pip install PyPDF2")
        sys.exit(1)
    
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        sys.exit(1)
    
    return text


def read_input_file(file_path: str) -> str:
    """Read from file, automatically handling PDF vs text files."""
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.pdf':
        print(f"Processing PDF file: {file_path}")
        return read_pdf_file(file_path)
    else:
        # Assume it's a text file
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)


def save_to_csv(results: List[TestResult], metadata: Dict[str, str], output_file: str):
    """Save results to a CSV file."""
    with open(output_file, 'w', newline='') as csvfile:
        # Write metadata
        writer = csv.writer(csvfile)
        writer.writerow(['Metadata'])
        for key, value in metadata.items():
            writer.writerow([key, value])
        
        writer.writerow([])  # Blank row
        
        # Write results
        writer.writerow(['Test Name', 'Test Method', 'Unit', 'Value', 'Specification', 'Result'])
        for result in results:
            writer.writerow([
                result.name, 
                result.method, 
                result.unit, 
                result.value, 
                result.specification, 
                result.result
            ])
        
        writer.writerow([])  # Blank row
        
        # Write summary
        passes = sum(1 for r in results if r.result == "PASS")
        fails = sum(1 for r in results if r.result == "FAIL")
        unknowns = sum(1 for r in results if r.result == "UNKNOWN")
        
        writer.writerow(['Summary'])
        writer.writerow(['Total Tests', len(results)])
        writer.writerow(['PASS', passes])
        writer.writerow(['FAIL', fails])
        writer.writerow(['UNKNOWN', unknowns])
        
        if fails > 0:
            writer.writerow([])
            writer.writerow(['Failed Tests'])
            for result in results:
                if result.result == "FAIL":
                    writer.writerow([result.name, result.value, result.specification]) 