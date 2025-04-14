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
- Modern GUI interface

## Installation

### For End Users (Windows)

1. Download the latest installer (`COA_Analyzer_Setup.exe`) from the releases page
2. Run the installer
3. The installer will:
   - Check system requirements
   - Install any missing dependencies (Python, Tesseract OCR, Visual C++ Redistributable)
   - Install the application
   - Create start menu and desktop shortcuts

System Requirements:
- Windows 7 SP1 or later
- 500MB free disk space
- Internet connection (for dependency installation)

### For Developers

#### Prerequisites
- Python 3.8 or later
- Poetry (Python package manager)
- Tesseract OCR
- Visual C++ Redistributable

#### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/coa-analyzer.git
cd coa-analyzer
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Install Tesseract OCR:
   - Windows: Download and install from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

4. Activate the virtual environment:
```bash
poetry shell
```

5. Run the application:
```bash
poetry run coa-analyzer
```

### Building from Source

To build the Windows installer:

1. Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isdl.php)

2. Build the executable:
```bash
poetry install
poetry run python build_script.py
```

3. Compile the installer:
   - Open `installer_script.iss` in Inno Setup
   - Click "Compile" to create the installer

## Usage

### GUI Mode
1. Launch the application from the start menu or desktop shortcut
2. Use the file browser to select a COA file (PDF or text)
3. View results in the application window
4. Export results to CSV if needed

### Command Line Mode
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
2. **PDF files** (.pdf): PDF documents containing COA information

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

## Troubleshooting

Common issues and solutions:

1. **Tesseract OCR not found**
   - Ensure Tesseract is installed in the default location
   - Add Tesseract to your system PATH
   - Restart the application

2. **Missing Visual C++ Redistributable**
   - Run the installer again to install dependencies
   - Download and install from Microsoft's website

3. **Application fails to start**
   - Check the log file in the application directory
   - Ensure all dependencies are installed
   - Try reinstalling the application

## License

This project is open source and available under the MIT License. 