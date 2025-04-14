import re
import sys
import argparse
import csv
import os
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

# Third-party imports
try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 package not found. Please install it using 'pip install PyPDF2'")
    sys.exit(1)

try:
    import pdf2image
except ImportError:
    print("Error: pdf2image package not found. Please install it using 'pip install pdf2image'")
    sys.exit(1)

try:
    import pytesseract
except ImportError:
    print("Error: pytesseract package not found. Please install it using 'pip install pytesseract'")
    sys.exit(1)

from logging.handlers import RotatingFileHandler

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('coa_processing.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


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
    if not value_str or not spec_str:
        return "UNKNOWN"  # Can't evaluate without value or specification
        
    try:
        # Clean and normalize value string
        value_str = value_str.strip().replace(',', '')
        value = float(value_str)
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not convert value '{value_str}' to float: {str(e)}")
        return "UNKNOWN"  # Non-numeric values can't be evaluated
    
    try:
        min_val, max_val = parse_specification(spec_str)
        
        if min_val is not None and value < min_val:
            return "FAIL"
        if max_val is not None and value > max_val:
            return "FAIL"
        if (min_val is None and max_val is None):
            logger.debug(f"Specification '{spec_str}' could not be parsed into min/max values")
            return "UNKNOWN"  # Can't evaluate without specification
    except Exception as e:
        logger.error(f"Error evaluating result for value '{value_str}' with spec '{spec_str}': {str(e)}", exc_info=True)
        return "UNKNOWN"
    
    return "PASS"


def extract_coa_data(raw_text: str) -> List[TestResult]:
    """Extract test data from COA text."""
    if not raw_text:
        logger.warning("Empty text provided to extract_coa_data")
        return []
        
    try:
        lines = raw_text.strip().split('\n')
        results = []
        seen_test_results = set()  # Track unique test results
        
        # Safety check for very large input
        if len(lines) > 10000:
            logger.warning(f"Input text is very large ({len(lines)} lines), truncating to first 10000 lines")
            lines = lines[:10000]
        
        # Find all COA sections
        coa_sections = []
        start_idx = -1
        
        for i, line in enumerate(lines):
            if "CERTIFICATE OF ANALYSIS" in line:
                if start_idx != -1:
                    coa_sections.append((start_idx, i))
                start_idx = i
        
        if start_idx != -1:
            coa_sections.append((start_idx, len(lines)))
        
        if not coa_sections:
            logger.warning("No 'CERTIFICATE OF ANALYSIS' header found in text")
            # Try to process the whole text as one section
            coa_sections = [(0, len(lines))]
        
        # Process each COA section
        for start_idx, end_idx in coa_sections:
            section_lines = lines[start_idx:end_idx]
            
            # Find the test results section
            test_names = []
            test_methods = []
            units = []
            values = []
            specs = []
            
            # Current section being read
            current_section = None
            
            # Process lines in this COA section
            for line in section_lines:
                try:
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
                except Exception as line_error:
                    logger.error(f"Error processing line '{line}': {str(line_error)}")
                    continue
            
            # Create test results from the collected data
            for i in range(len(test_names)):
                try:
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
                    
                    # Create unique key for this test result
                    result_key = f"{name}_{method}_{value}_{spec}"
                    if result_key in seen_test_results:
                        continue
                    
                    seen_test_results.add(result_key)
                    result = evaluate_result(value, spec)
                    
                    results.append(TestResult(
                        name=name,
                        method=method,
                        unit=unit,
                        value=value,
                        specification=spec,
                        result=result
                    ))
                except Exception as result_error:
                    logger.error(f"Error creating test result at index {i}: {str(result_error)}")
                    continue
        
        return results
        
    except Exception as e:
        logger.error(f"Error in extract_coa_data: {str(e)}", exc_info=True)
        return []


def extract_metadata(raw_text: str) -> Dict[str, str]:
    """Extract metadata from the COA text."""
    if not raw_text:
        logger.warning("Empty text provided to extract_metadata")
        return {"Batch": "N/A"}
        
    try:
        metadata = {}
        lines = raw_text.strip().split('\n')
        
        # Safety check for very large input
        if len(lines) > 10000:
            logger.warning(f"Input text is very large ({len(lines)} lines), truncating to first 10000 lines")
            lines = lines[:10000]
        
        # Extract material information
        try:
            material_pattern = re.compile(r'Material:?\s*([A-Z0-9]+\s+[A-Z0-9\s]+(?:CHP|GRT|GNA)\s+[A-Z0-9\s]+)')
            reference_pattern = re.compile(r'(?:Reference No:|CPN:|Sales Order No\.|Order No\.?)\s*([A-Z0-9]+)')
        except re.error as pattern_error:
            logger.error(f"Error compiling regex pattern: {str(pattern_error)}")
            material_pattern = re.compile(r'Material:?\s*(\S+)')
            reference_pattern = re.compile(r'Reference No:\s*(\S+)')
        
        # Enhanced batch pattern to handle more formats - compile with error handling
        batch_patterns = []
        try:
            batch_patterns = [
                re.compile(r'(?:Batch|Lot|Batch No\.?|Batch Number)\s*[:.]?\s*([0-9A-Z]+(?:[A-Z][0-9]+)?)', re.IGNORECASE),
                re.compile(r'(?:Batch|Lot)\s*ID\s*[:.]?\s*([0-9A-Z]+(?:[A-Z][0-9]+)?)', re.IGNORECASE),
                re.compile(r'^\s*([0-9]{6}[A-Z][0-9]{3})\s*$'),  # Format like: 241226D257
                re.compile(r'(?:Batch|Lot)\s*#\s*[:.]?\s*([0-9A-Z]+(?:[A-Z][0-9]+)?)', re.IGNORECASE),
                re.compile(r'(?:Batch|Lot)\s*:\s*([0-9A-Z]+(?:[A-Z][0-9]+)?)', re.IGNORECASE),
                re.compile(r'(?:Batch|Lot)\s*=\s*([0-9A-Z]+(?:[A-Z][0-9]+)?)', re.IGNORECASE),
                re.compile(r'Batch\s+([0-9]{6}[A-Z][0-9]{3})\s+[0-9,]+\s*/LB', re.IGNORECASE),  # Format from delivery note
                re.compile(r'Batch\s+([0-9]{6}[A-Z][0-9]{3})', re.IGNORECASE),  # Simpler delivery note format
                re.compile(r'Batch\s*\n\s*([0-9]{6}[A-Z][0-9]{3})', re.IGNORECASE),  # Format with newline
                re.compile(r'Batch\s*\n\s*([0-9A-Z]+)', re.IGNORECASE),  # Generic format with newline
                re.compile(r'(?:Batch|Lot)\s*\n\s*([0-9]{6}[A-Z][0-9]{3})\s*\n', re.IGNORECASE),  # OCR format with newlines
                re.compile(r'(?:Batch|Lot)\s*\n\s*([0-9A-Z]+)\s*\n', re.IGNORECASE),  # Generic OCR format with newlines
                re.compile(r'(?:Batch|Lot)\s*\n([0-9]{6}[A-Z][0-9]{3})', re.IGNORECASE),  # OCR format with single newline
                re.compile(r'(?:Batch|Lot)\s*\n([0-9A-Z]+)', re.IGNORECASE)  # Generic OCR format with single newline
            ]
        except re.error as pattern_error:
            logger.error(f"Error compiling batch pattern: {str(pattern_error)}")
            # Use simpler patterns as fallback
            batch_patterns = [
                re.compile(r'Batch\s*[:.]?\s*([0-9A-Z]+)', re.IGNORECASE),
                re.compile(r'Lot\s*[:.]?\s*([0-9A-Z]+)', re.IGNORECASE)
            ]
        
        batch_found = False
        logger.debug("Starting metadata extraction...")
        logger.debug(f"Total lines to process: {len(lines)}")
        
        # First pass: look for batch number in standard format
        for i, line in enumerate(lines):
            try:
                logger.debug(f"\nProcessing line {i}: '{line}'")
                
                # Look for material info
                if material_match := material_pattern.search(line):
                    metadata["Material"] = material_match.group(1).strip()
                    logger.debug(f"Found material: {metadata['Material']}")
                    continue
                
                # Look for reference number
                if reference_match := reference_pattern.search(line):
                    metadata["Reference"] = reference_match.group(1).strip()
                    logger.debug(f"Found reference: {metadata['Reference']}")
                    continue
                
                # Try all batch patterns
                if not batch_found:
                    # Try single line patterns
                    for pattern_idx, pattern in enumerate(batch_patterns):
                        try:
                            if batch_match := pattern.search(line):
                                metadata["Batch"] = batch_match.group(1).strip()
                                batch_found = True
                                logger.debug(f"Found batch number using pattern {pattern_idx}: {metadata['Batch']}")
                                logger.debug(f"Pattern used: {pattern.pattern}")
                                break
                        except (re.error, IndexError) as e:
                            logger.error(f"Error using pattern {pattern_idx}: {str(e)}")
                            continue
                    
                    # Try multi-line patterns if we're not at the last line
                    if not batch_found and i < len(lines) - 2:
                        try:
                            three_lines = '\n'.join(lines[i:i+3])
                            logger.debug(f"Trying multi-line pattern with lines:\n{three_lines}")
                            for pattern_idx, pattern in enumerate(batch_patterns):
                                try:
                                    if batch_match := pattern.search(three_lines):
                                        metadata["Batch"] = batch_match.group(1).strip()
                                        batch_found = True
                                        logger.debug(f"Found batch number using multi-line pattern {pattern_idx}: {metadata['Batch']}")
                                        logger.debug(f"Pattern used: {pattern.pattern}")
                                        break
                                except (re.error, IndexError) as e:
                                    logger.error(f"Error using multi-line pattern {pattern_idx}: {str(e)}")
                                    continue
                        except Exception as e:
                            logger.error(f"Error processing multi-line pattern: {str(e)}")
                    
                    if batch_found:
                        continue
                
                # Look for production date and country
                if "DATE OF PRODUCTION" in line:
                    parts = re.split(r'\s{2,}', line)
                    if len(parts) > 1:
                        metadata["Production Date"] = parts[-1].strip()
                        logger.debug(f"Found production date: {metadata['Production Date']}")
                    continue
                
                if "COUNTRY OF ORIGIN" in line:
                    parts = re.split(r'\s{2,}', line)
                    if len(parts) > 1:
                        metadata["Country"] = parts[-1].strip()
                        logger.debug(f"Found country: {metadata['Country']}")
            except Exception as line_error:
                logger.error(f"Error processing line {i}: {str(line_error)}")
                continue
        
        # Second pass: if no batch found, look for standalone batch number
        if "Batch" not in metadata:
            try:
                logger.debug("\nNo batch found in first pass, trying second pass...")
                batch_idx = -1
                qty_idx = -1
                
                for i, line in enumerate(lines):
                    try:
                        line_upper = line.upper()
                        if any(x in line_upper for x in ["BATCH", "LOT"]):
                            batch_idx = i
                            logger.debug(f"Found batch header at line {i}: '{line}'")
                            # Check the next line for a batch number
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                logger.debug(f"Checking next line for batch number: '{next_line}'")
                                if re.match(r'^[0-9]{6}[A-Z][0-9]{3}$', next_line):
                                    metadata["Batch"] = next_line
                                    batch_found = True
                                    logger.debug(f"Found batch number in next line: {metadata['Batch']}")
                                    break
                        elif "QTY" in line_upper:
                            qty_idx = i
                            logger.debug(f"Found qty header at line {i}: '{line}'")
                            break
                    except Exception as line_error:
                        logger.error(f"Error in second pass line {i}: {str(line_error)}")
                        continue
                
                if not batch_found and batch_idx != -1 and qty_idx != -1:
                    logger.debug(f"\nLooking between lines {batch_idx+1} and {qty_idx}")
                    # Look at lines between batch and qty
                    for line in lines[batch_idx+1:qty_idx]:
                        try:
                            line = line.strip()
                            logger.debug(f"Checking line between batch and qty: '{line}'")
                            if re.match(r'^[0-9A-Z]+(?:[A-Z][0-9]+)?$', line):
                                metadata["Batch"] = line
                                batch_found = True
                                logger.debug(f"Found standalone batch number: {metadata['Batch']}")
                                break
                        except Exception as e:
                            logger.error(f"Error checking batch-qty line: {str(e)}")
                            continue
            except Exception as second_pass_error:
                logger.error(f"Error in second pass: {str(second_pass_error)}")
        
        if "Batch" not in metadata:
            logger.warning("No batch number found in the document")
            metadata["Batch"] = "N/A"  # Set default value if no batch number found
        else:
            logger.info(f"Successfully extracted batch number: {metadata['Batch']}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error in extract_metadata: {str(e)}", exc_info=True)
        return {"Batch": "N/A"}


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
        writer = csv.writer(csvfile)
        
        # Write metadata header
        writer.writerow(['Metadata'])
        
        # Write metadata in a specific order for consistency
        metadata_order = ['Material', 'Reference', 'Batch', 'Production Date', 'Country']
        for key in metadata_order:
            if key in metadata:
                writer.writerow([key, metadata[key]])
            elif key == 'Batch':
                writer.writerow(['Batch', 'N/A'])  # Always include batch number, even if not found
        
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


def is_coa_page(text: str) -> bool:
    """Determine if a page contains COA data."""
    # Check for common COA indicators
    indicators = [
        "CERTIFICATE OF ANALYSIS",
        "Test Name",
        "Test Method",
        "Unit",
        "Value",
        "Specification",
        "Batch",
        "Material:",
        "Reference No:"
    ]
    
    # Count how many indicators are present
    matches = sum(1 for indicator in indicators if indicator in text)
    
    # If we find at least 3 indicators, it's likely a COA page
    return matches >= 3


def read_pdf_file(file_path: str) -> str:
    """Extract text from a PDF file."""
    logger.debug(f"Starting PDF processing for: {file_path}")
    reader = None
    coa_text = ""
    
    try:
        # First try regular text extraction
        reader = PyPDF2.PdfReader(file_path)
        
        # Process each page
        for page in reader.pages:
            text = page.extract_text()
            if is_coa_page(text):
                coa_text += text + "\n\n"
        
        if coa_text.strip():
            logger.debug("Successfully extracted text from PDF")
            # Explicitly close and release PDF resources
            reader = None
            return coa_text
        
        # If no text was extracted, try OCR
        logger.debug("No text found in PDF, attempting OCR...")
        import tempfile
        with tempfile.TemporaryDirectory() as path:
            try:
                # Convert PDF to images
                images = pdf2image.convert_from_path(file_path)
                ocr_text = ""
                
                # Process each image with OCR
                for i, image in enumerate(images):
                    temp_file = os.path.join(path, f'page_{i}.png')
                    try:
                        # Save image to temp file
                        image.save(temp_file, 'PNG')
                        # Process with OCR
                        page_text = pytesseract.image_to_string(temp_file)
                        
                        if is_coa_page(page_text):
                            ocr_text += page_text + "\n\n"
                            
                        # Explicitly delete the image from memory after processing
                        del page_text
                        # Explicitly remove temp file after processing
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except:
                                pass
                    except Exception as e:
                        logger.error(f"Error processing page {i}: {e}")
                    finally:
                        # Make sure image is released
                        image = None
                
                # Release all images
                del images
                
                # Return OCR text if any was found
                if ocr_text.strip():
                    return ocr_text
                else:
                    logger.warning("OCR completed but no text was extracted")
                    return ""
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                return ""
            finally:
                # Extra cleanup to ensure tempdir gets cleared
                import gc
                gc.collect()
    except Exception as e:
        logger.error(f"Error reading PDF file: {e}")
        return ""
    finally:
        # Final cleanup
        reader = None
        import gc
        gc.collect()


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


def print_summary_table(results_list: List[Tuple[str, List[TestResult], Dict[str, str]]]):
    """Print a summary table of all processed PDFs and their results."""
    print("\nSummary of All Processed COAs:")
    print("=" * 100)
    print(f"{'File Name':<30} {'Material':<20} {'Batch':<15} {'Tests':<8} {'Pass':<8} {'Fail':<8}")
    print("-" * 100)
    
    total_tests = 0
    total_pass = 0
    total_fail = 0
    
    for filename, results, metadata in results_list:
        # Get just the filename without path
        base_filename = os.path.basename(filename)
        
        # Count results
        passes = sum(1 for r in results if r.result == "PASS")
        fails = sum(1 for r in results if r.result == "FAIL")
        
        # Get metadata
        material = metadata.get("Material", "").split()[0] if metadata.get("Material") else "N/A"
        batch = metadata.get("Batch", "N/A")
        
        # Print row
        print(f"{base_filename[:30]:<30} {material[:20]:<20} {batch[:15]:<15} "
              f"{len(results):<8} {passes:<8} {fails:<8}")
        
        # Update totals
        total_tests += len(results)
        total_pass += passes
        total_fail += fails
    
    print("-" * 100)
    print(f"{'TOTAL':<30} {'':<20} {'':<15} {total_tests:<8} {total_pass:<8} {total_fail:<8}")
    print("=" * 100)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Certificate of Analysis (COA) Analyzer')
    parser.add_argument('-i', '--input', help='Input file containing COA text (txt or pdf)', required=False)
    parser.add_argument('-o', '--output', help='Output CSV file for results', required=False)
    parser.add_argument('-v', '--visualize', help='Show ASCII visualization of results', action='store_true')
    parser.add_argument('-d', '--debug', help='Enable debug logging', action='store_true')
    parser.add_argument('-b', '--batch', help='Process all PDFs in a directory', action='store_true')
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    all_results = []
    
    if args.batch:
        # Process all PDFs in the directory of the input file
        input_dir = args.input if args.input else "."
        if not os.path.isdir(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            sys.exit(1)
            
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(input_dir, filename)
                logger.info(f"\nProcessing {filename}...")
                
                # Process the file
                coa_text = read_input_file(filepath)
                if not coa_text.strip():
                    logger.error(f"No COA data found in {filename}")
                    continue
                
                # Extract data
                results = extract_coa_data(coa_text)
                metadata = extract_metadata(coa_text)
                
                # Save results if output specified
                if args.output:
                    output_file = f"{os.path.splitext(filepath)[0]}_results.csv"
                    save_to_csv(results, metadata, output_file)
                    logger.info(f"Results saved to {output_file}")
                
                all_results.append((filepath, results, metadata))
        
        # Print summary table
        if all_results:
            print_summary_table(all_results)
    
    else:
        # Process single file
        if args.input:
            coa_text = read_input_file(args.input)
            if not coa_text.strip():
                logger.error("No COA data found in the input file")
                sys.exit(1)
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
COUNTRY OF ORIGIN                           US
"""
            logger.info("Using sample COA data. Use --input to specify a file.")
        
        # Extract data
        results = extract_coa_data(coa_text)
        metadata = extract_metadata(coa_text)
        
        # Print results
        print_results(results, metadata, show_ascii_viz=args.visualize)
        
        # Save to CSV if output file specified
        if args.output:
            save_to_csv(results, metadata, args.output)
            logger.info(f"Results saved to {args.output}")
        
        all_results.append((args.input or "sample", results, metadata))
        
        # Print summary table
        print_summary_table(all_results)


if __name__ == "__main__":
    main()
