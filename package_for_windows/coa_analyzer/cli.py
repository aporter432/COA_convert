"""Command-line interface for COA Analyzer."""

import argparse
import sys

from .core import extract_coa_data, extract_metadata
from .display import print_results
from .io import read_input_file, save_to_csv


def get_sample_coa() -> str:
    """Return a sample COA for demo purposes."""
    return """
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


def main():
    """Main entry point for the command-line interface."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Certificate of Analysis (COA) Analyzer')
    parser.add_argument('-i', '--input', help='Input file containing COA text (txt or pdf)', required=False)
    parser.add_argument('-o', '--output', help='Output CSV file for results', required=False)
    parser.add_argument('-v', '--visualize', help='Show ASCII visualization of results', action='store_true')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    
    args = parser.parse_args()
    
    # Get COA text from file or use sample
    if args.input:
        coa_text = read_input_file(args.input)
    else:
        # Use sample COA text
        coa_text = get_sample_coa()
        print("Using sample COA data. Use --input to specify a file.")
    
    # Extract data
    results = extract_coa_data(coa_text)
    if not results:
        print("Error: No valid test results found in the input.")
        sys.exit(1)
        
    metadata = extract_metadata(coa_text)
    
    # Print results
    print_results(results, metadata, show_ascii_viz=args.visualize)
    
    # Save to CSV if output file specified
    if args.output:
        save_to_csv(results, metadata, args.output)
        print(f"\nResults saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 