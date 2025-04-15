"""Display functions for COA Analyzer."""

import sys
from typing import Dict, List

from .core import TestResult, parse_specification


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