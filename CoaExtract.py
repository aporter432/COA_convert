import re
import sys
import argparse
import csv
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict


@dataclass
class TestResult:
    name: str
    method: str
    unit: str
    value: str
    specification: str
    result: str  # PASS or FAIL


def parse_specification(spec_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse specification string into min and max values."""
    if not spec_str or spec_str == "N/A":
        return None, None
    
    # Handle "= < X.XX" format
    if match := re.match(r'=\s*<\s*(\d+\.?\d*)', spec_str):
        return None, float(match.group(1))
    
    # Handle "= > X.XX" format
    if match := re.match(r'=\s*>\s*(\d+\.?\d*)', spec_str):
        return float(match.group(1)), None
    
    # Handle "X.XX - Y.YY" format
    if match := re.match(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', spec_str):
        return float(match.group(1)), float(match.group(2))
    
    # Handle "- Y.YY" format (missing min value)
    if match := re.match(r'-\s*(\d+\.?\d*)', spec_str):
        return None, float(match.group(1))
    
    return None, None


def evaluate_result(value_str: str, spec_str: str) -> str:
    """Evaluate if a value passes the specification."""
    try:
        value = float(value_str)
    except ValueError:
        return "UNKNOWN"  # Non-numeric values can't be evaluated
    
    min_val, max_val = parse_specification(spec_str)
    
    if min_val is not None and value < min_val:
        return "FAIL"
    if max_val is not None and value > max_val:
        return "FAIL"
    if (min_val is None and max_val is None):
        return "UNKNOWN"  # Can't evaluate without specification
    
    return "PASS"


def extract_coa_data(raw_text: str) -> List[TestResult]:
    """Extract test data from COA text."""
    lines = raw_text.strip().split('\n')
    results = []
    
    # Find the Certificate of Analysis section
    coa_start = -1
    for i, line in enumerate(lines):
        if "CERTIFICATE OF ANALYSIS" in line:
            coa_start = i
            break
    
    if coa_start == -1:
        return []  # No COA section found
    
    # Find the test results section
    test_names = []
    test_methods = []
    units = []
    values = []
    specs = []
    
    # Current section being read
    current_section = None
    
    # Process lines after COA header
    for line in lines[coa_start:]:
        line = line.strip()
        if not line:
            continue
            
        # Skip metadata lines
        if any(x in line for x in ["Batch", "Qty /Uom", "Material:", "Our/Customer Reference", "Page", "THE PRODUCT"]):
            continue
            
        # Check for section headers
        if "Test Name" in line:
            current_section = "names"
            continue
        elif "Test Method" in line:
            current_section = "methods"
            continue
        elif "Unit" in line:
            current_section = "units"
            continue
        elif "Value" in line:
            current_section = "values"
            continue
        elif "Specification" in line:
            current_section = "specs"
            continue
            
        # Add data to appropriate list if it looks valid
        if current_section == "names" and re.match(r'^[A-Za-z0-9\']+', line):
            if line not in ["DATE OF PRODUCTION", "COUNTRY OF ORIGIN"]:
                test_names.append(line)
        elif current_section == "methods" and re.match(r'^N200\.\d+', line):
            test_methods.append(line)
        elif current_section == "units" and line in ["dNm", "min.", "%", "min"]:
            units.append(line)
        elif current_section == "values" and re.match(r'^\d+\.?\d*$', line):
            values.append(line)
        elif current_section == "specs" and ("=" in line or "-" in line or any(x in line for x in ["<", ">"])):
            specs.append(line)
    
    # Create test results from the collected data
    for i in range(len(test_names)):
        name = test_names[i]
        method = test_methods[i] if i < len(test_methods) else ""
        unit = units[i] if i < len(units) else ""
        value = values[i] if i < len(values) else ""
        spec = specs[i] if i < len(specs) else ""
        
        # Skip non-test entries
        if name in ["DATE OF PRODUCTION", "COUNTRY OF ORIGIN"]:
            continue
            
        # Handle special cases
        if name == "ML100" and not unit:
            unit = ""  # ML100 typically has no unit
        
        result = evaluate_result(value, spec)
        
        results.append(TestResult(
            name=name,
            method=method,
            unit=unit,
            value=value,
            specification=spec,
            result=result
        ))
    
    return results


def extract_metadata(raw_text: str) -> Dict[str, str]:
    """Extract metadata from the COA text."""
    metadata = {}
    lines = raw_text.strip().split('\n')
    
    # Extract material information
    for line in lines:
        if "Material:" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                metadata["Material"] = parts[1].strip()
        
        elif "Reference No:" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                metadata["Reference"] = parts[1].strip()
        
        elif "Batch" in line:
            # Look for batch information in next line
            batch_idx = lines.index(line)
            if batch_idx + 1 < len(lines) and lines[batch_idx + 1].strip():
                metadata["Batch"] = lines[batch_idx + 1].strip()
    
    # Look for production date and country
    for i, line in enumerate(lines):
        if "DATE OF PRODUCTION" in line:
            parts = re.split(r'\s{2,}', line)
            if len(parts) > 1:
                metadata["Production Date"] = parts[-1].strip()
        
        elif "COUNTRY OF ORIGIN" in line:
            parts = re.split(r'\s{2,}', line)
            if len(parts) > 1:
                metadata["Country"] = parts[-1].strip()
    
    return metadata


def print_results(results: List[TestResult], metadata: Dict[str, str], show_ascii_viz: bool = False):
    """Print the analysis results to console."""
    # Print metadata
    print("\nCOA Metadata:")
    print("-" * 80)
    for key, value in metadata.items():
        print(f"{key}: {value}")
    
    # Print test results
    print("\nCOA Analysis Results:")
    print("-" * 80)
    print(f"{'Test Name':<20} {'Value':<10} {'Specification':<20} {'Result':<10}")
    print("-" * 80)
    
    for result in results:
        result_display = result.result
        # Add color indicators for terminal if supported
        if sys.stdout.isatty():
            if result.result == "PASS":
                result_display = f"\033[92m{result.result}\033[0m"  # Green
            elif result.result == "FAIL":
                result_display = f"\033[91m{result.result}\033[0m"  # Red
            elif result.result == "UNKNOWN":
                result_display = f"\033[93m{result.result}\033[0m"  # Yellow
                
        print(f"{result.name:<20} {result.value:<10} {result.specification:<20} {result_display:<10}")
    
    # Print ASCII visualization if requested
    if show_ascii_viz:
        print("\nResult Visualization:")
        print("-" * 80)
        bar_width = 50
        
        for result in results:
            # Create a visual bar
            bar_str = ""
            if result.result == "PASS":
                bar_str = "█" * bar_width
                indicator = "✓"
            elif result.result == "FAIL":
                bar_str = "▒" * bar_width
                indicator = "✗"
            else:
                bar_str = "░" * bar_width
                indicator = "?"
            
            # Try to show where the value falls within specification
            min_val, max_val = parse_specification(result.specification)
            try:
                value = float(result.value)
                if min_val is not None and max_val is not None:
                    # For range specifications
                    range_size = max_val - min_val
                    if range_size > 0:
                        position = int(((value - min_val) / range_size) * bar_width)
                        position = max(0, min(bar_width - 1, position))
                        bar_list = list(bar_str)
                        bar_list[position] = '|'
                        bar_str = ''.join(bar_list)
            except (ValueError, TypeError):
                pass
            
            print(f"{result.name:<15} [{bar_str}] {indicator}")
    
    # Summary
    passes = sum(1 for r in results if r.result == "PASS")
    fails = sum(1 for r in results if r.result == "FAIL")
    unknowns = sum(1 for r in results if r.result == "UNKNOWN")
    
    print("\nSummary:")
    print(f"Total Tests: {len(results)}")
    print(f"PASS: {passes}")
    print(f"FAIL: {fails}")
    print(f"UNKNOWN: {unknowns}")
    
    if fails > 0:
        print("\nFailed Tests:")
        for result in results:
            if result.result == "FAIL":
                print(f"- {result.name}: {result.value} (Spec: {result.specification})")


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


def read_pdf_file(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        # First try regular text extraction
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        # If we got text, return it
        if text.strip():
            return text
        
        # If no text was extracted, try OCR
        print("No text found in PDF, attempting OCR...")
        from pdf2image import convert_from_path
        import pytesseract
        import tempfile
        import os
        
        # Convert PDF to images
        with tempfile.TemporaryDirectory() as path:
            images = convert_from_path(file_path)
            text = ""
            
            # Process each page
            for i, image in enumerate(images):
                # Save the image temporarily
                temp_file = os.path.join(path, f'page_{i}.png')
                image.save(temp_file, 'PNG')
                
                # Extract text using OCR
                page_text = pytesseract.image_to_string(temp_file)
                text += page_text
                text += "\n\n"  # Add spacing between pages
                
                # Debug output
                print(f"\nOCR Output for page {i+1}:")
                print("-" * 80)
                print(page_text)
                print("-" * 80)
        
        return text
        
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        sys.exit(1)


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


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Certificate of Analysis (COA) Analyzer')
    parser.add_argument('-i', '--input', help='Input file containing COA text (txt or pdf)', required=False)
    parser.add_argument('-o', '--output', help='Output CSV file for results', required=False)
    parser.add_argument('-v', '--visualize', help='Show ASCII visualization of results', action='store_true')
    args = parser.parse_args()
    
    # Get COA text from file or use sample
    if args.input:
        coa_text = read_input_file(args.input)
    else:
        # Use sample COA text
        coa_text = """
Material: D14924998 NEOPRENE GNA M2 CHP 100 ABAG25KG
Our/Customer Reference No: S030068A

Batch
241226D257
Qty / Uom
2,205.000 /LB

Test Name           Test Method    Unit     Value         Specification
s'TPOINT90          N200.7405      dNm      11.73         7.50 - 12.50
TIME SCORCH01       N200.7405      min.     2.47          1.60 - 3.60
VOLATILE            N200.9500      %        0.99          = < 1.30
TIME TPOINT90       N200.7405      min.     4.84          2.10 - 7.60
ML100               N200.5700                53            47 - 59
ML120               N200.7460      min.     38.04         = > 11.00
DATE OF PRODUCTION                           20241229
COUNTRY OF ORIGIN                            US
"""
        print("Using sample COA data. Use --input to specify a file.")
    
    # Extract data
    results = extract_coa_data(coa_text)
    metadata = extract_metadata(coa_text)
    
    # Print results
    print_results(results, metadata, show_ascii_viz=args.visualize)
    
    # Save to CSV if output file specified
    if args.output:
        save_to_csv(results, metadata, args.output)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
