# Certificate of Analysis (COA) Analyzer

A Python utility for extracting and evaluating test results from Certificate of Analysis (COA) documents.

## Features

- Parses COA text from input files or standard input
- Supports both text files and PDF documents
- Extracts test values and specifications
- Evaluates test results against specification thresholds for pass/fail status
- Handles various specification formats:
  - Range formats (e.g., "7.50 - 12.50")
  - Maximum thresholds (e.g., "= < 1.30")
  - Minimum thresholds (e.g., "= > 11.00")
- Provides ASCII visualization of test results
- Exports results to CSV format
- Color-coded terminal output

## Installation

### Basic Installation
The script can run with standard Python libraries for text file processing. No external dependencies are required for basic functionality.

### PDF Support
To enable PDF support, install the PyPDF2 library:

```bash
# Create a virtual environment (recommended)
python3 -m venv coa_venv
source coa_venv/bin/activate  # On Windows: coa_venv\Scripts\activate

# Install PyPDF2
pip install PyPDF2
```

## Usage

```
python3 CoaExtract.py [-h] [-i INPUT] [-o OUTPUT] [-v]

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input file containing COA text (txt or pdf)
  -o OUTPUT, --output OUTPUT
                        Output CSV file for results
  -v, --visualize       Show ASCII visualization of results
```

### Examples

#### Process a sample COA with built-in example:
```
python3 CoaExtract.py
```

#### Process a COA file and visualize results:
```
python3 CoaExtract.py -i sample_coa.txt -v
```

#### Process a PDF COA and save results to CSV:
```
python3 CoaExtract.py -i certificate.pdf -o results.csv
```

## Input Format

The script accepts the following input formats:

1. **Plain text files** (.txt): Text files containing COA data in a tabular structure
2. **PDF files** (.pdf): PDF documents containing COA information (requires PyPDF2)

Example text format:

```
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
```

## Output

The script outputs:
1. Metadata extracted from the COA
2. Table of test results with pass/fail status
3. Optional ASCII visualization of results
4. Summary of pass/fail counts
5. List of failed tests (if any)

If an output file is specified, the results are saved to a CSV file with the same information.

## Future Enhancements

Potential improvements to consider:
- OCR integration for processing scanned COA documents
- Support for additional file formats (XLSX, DOC)
- Web interface for uploading and processing COAs
- Historical tracking of COA results
- Statistical analysis of trends
- Batch processing of multiple COA files

## License

This project is open source and available under the MIT License. 