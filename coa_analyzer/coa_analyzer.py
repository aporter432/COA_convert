"""COA Analyzer GUI module for analyzing Certificate of Analysis documents."""

import sys
import os
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                           QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from coa_analyzer.coa_extract import extract_coa_data, extract_metadata, read_input_file, save_to_csv
from typing import cast, TypeGuard

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

def is_valid_path(path: str | None) -> TypeGuard[str]:
    return isinstance(path, str) and bool(path)

class COAAnalyzer(QMainWindow):
    """Main window class for the COA Analyzer application.
    
    This class provides a GUI interface for analyzing Certificate of Analysis (COA) 
    documents. It supports drag-and-drop functionality for PDF files and displays 
    results in both table and detailed text formats.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize instance variables
        self.results: list = []
        self.metadata: dict = {}
        self.current_file: str | None = None
        
        # Set up the main window
        self.setWindowTitle("COA Analyzer")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "File Name", "Material", "Batch", "Tests", "Pass", "Fail"
        ])
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Create detailed results area
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details)
        
        # Set up drag and drop
        self.setAcceptDrops(True)
        
        logger.debug("COAAnalyzer initialization complete")
        
    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        if event is None:
            return
        mime_data = event.mimeData()
        if mime_data is None:
            return
        if mime_data.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent | None) -> None:
        if event is None:
            return
        mime_data = event.mimeData()
        if mime_data is None:
            return
        for url in mime_data.urls():
            file_path = url.toLocalFile()
            if file_path and file_path.lower().endswith('.pdf'):
                try:
                    self.process_file(file_path)
                except Exception as e:
                    logger.error(f"Error processing file: {e}", exc_info=True)
                    self.details.setText(f"Error: {str(e)}")
        event.acceptProposedAction()

    def process_file(self, file_path: str) -> None:
        """Process a COA file and display results."""
        try:
            if not is_valid_path(file_path):
                self.details.setText("Error: Invalid file path")
                return
                
            logger.debug(f"Processing file: {file_path}")
            raw_text = read_input_file(file_path)
            if not raw_text:
                self.details.setText("Could not read file")
                return
                
            results = extract_coa_data(raw_text)
            if not results:
                self.details.setText("No COA data found")
                return
                
            metadata = extract_metadata(raw_text)
            
            self.results = results
            self.metadata = metadata
            self.current_file = file_path
            
            self.update_table()
            self.show_details(file_path, results, metadata)
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            self.details.setText(f"Error: {str(e)}")
            self.results = []
            self.metadata = {}

    def update_table(self) -> None:
        """Update the results table with current data."""
        logger.debug("Updating results table")
        self.table.setRowCount(1)  # Only show one row per file
        
        # Get just the filename without path
        base_filename = os.path.basename(self.current_file) if self.current_file else "No file"
        
        # Count results
        passes = sum(1 for r in self.results if r.result == "PASS")
        fails = sum(1 for r in self.results if r.result == "FAIL")
        
        # Get metadata
        material = self.metadata.get("Material", "").split()[0] if self.metadata.get("Material") else "N/A"
        batch = self.metadata.get("Batch", "N/A")
        
        # Add items to table
        self.table.setItem(0, 0, QTableWidgetItem(base_filename))
        self.table.setItem(0, 1, QTableWidgetItem(material))
        self.table.setItem(0, 2, QTableWidgetItem(batch))
        self.table.setItem(0, 3, QTableWidgetItem(str(len(self.results))))
        self.table.setItem(0, 4, QTableWidgetItem(str(passes)))
        self.table.setItem(0, 5, QTableWidgetItem(str(fails)))
            
    def show_details(self, file_path: str, results: list, metadata: dict) -> None:
        """Display detailed results in the text area.
        
        Args:
            file_path: Path to the processed file
            results: List of test results
            metadata: Dictionary of metadata from the COA
        """
        logger.debug("Showing details")
        # Clear previous content
        self.details.clear()
        
        # File header with separator
        self.details.append(f"╔{'═' * 78}╗")
        self.details.append(f"║ {'Results for ' + os.path.basename(file_path):<76} ║")
        self.details.append(f"╚{'═' * 78}╝")
        
        self._show_metadata_section(metadata)
        self._show_results_section(results)
        
    def _show_metadata_section(self, metadata: dict) -> None:
        """Display the metadata section in the details area.
        
        Args:
            metadata: Dictionary of metadata from the COA
        """
        self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
        self.details.append("║ Metadata                                                                              ║")
        self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Calculate max key length for alignment
        max_key_len = max(len(key) for key in metadata.keys()) if metadata else 0
        
        for key, value in metadata.items():
            self.details.append(f"║ {key:<{max_key_len}} : {value:<{76-max_key_len-3}} ║")
        self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
        
    def _show_results_section(self, results: list) -> None:
        """Display the test results section in the details area.
        
        Args:
            results: List of test results
        """
        self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
        self.details.append("║ Test Results                                                                          ║")
        self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Filter out non-test entries and duplicates
        filtered_results = self._filter_results(results)
        
        # Calculate column widths
        name_width, value_width, spec_width = self._calculate_column_widths(filtered_results)
        
        # Display results
        self._display_results_table(filtered_results, name_width, value_width, spec_width)
        
    def _filter_results(self, results: list) -> list:
        """Filter out non-test entries and duplicates from results.
        
        Args:
            results: List of test results
            
        Returns:
            List of filtered test results
        """
        seen_tests = set()
        filtered_results = []
        
        for result in results:
            # Skip non-test entries
            if result.name in ["DATE OF PRODUCTION", "COUNTRY OF ORIGIN"]:
                continue
                
            # Skip entries without values or specifications
            if not result.value or not result.specification:
                continue
                
            # Create a unique key for this test
            test_key = f"{result.name}_{result.method}_{result.value}_{result.specification}"
            if test_key not in seen_tests:
                seen_tests.add(test_key)
                filtered_results.append(result)
                
        return filtered_results
        
    def _calculate_column_widths(self, results: list) -> tuple:
        """Calculate column widths for the results table.
        
        Args:
            results: List of test results
            
        Returns:
            Tuple of (name_width, value_width, spec_width)
        """
        if not results:
            return (20, 10, 20)  # Default sizes for empty results
            
        try:
            name_width = max((len(str(r.name)) for r in results if r.name is not None), default=20)
            value_width = max((len(str(r.value)) for r in results if r.value is not None), default=10)
            spec_width = max((len(str(r.specification)) for r in results if r.specification is not None), default=20)
            
            return (
                max(name_width, 20),  # Ensure minimum width
                max(value_width, 10),
                max(spec_width, 20)
            )
        except Exception:
            # Fall back to default values if calculation fails
            return (20, 10, 20)
        
    def _display_results_table(self, results: list, name_width: int, value_width: int, spec_width: int) -> None:
        """Display the results in a formatted table.
        
        Args:
            results: List of test results
            name_width: Width for the name column
            value_width: Width for the value column
            spec_width: Width for the specification column
        """
        if not results:
            self.details.append("║ No test results found                                                                 ║")
            self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
            return
            
        # Header
        try:
            header = f"║ {'Test Name':<{name_width}} │ {'Value':<{value_width}} │ {'Specification':<{spec_width}} │ {'Result':<6} ║"
            self.details.append(header)
            self.details.append(f"╟{'─' * name_width}┼{'─' * (value_width+2)}┼{'─' * (spec_width+2)}┼{'─' * 8}╢")
            
            # Results
            for result in results:
                try:
                    # Safely get values with fallbacks
                    name = str(result.name) if result.name is not None else "N/A"
                    value = str(result.value) if result.value is not None else "N/A"
                    spec = str(result.specification) if result.specification is not None else "N/A"
                    status = str(result.result) if result.result is not None else "UNKNOWN"
                    
                    row = f"║ {name:<{name_width}} │ {value:<{value_width}} │ {spec:<{spec_width}} │ {status:<6} ║"
                    self.details.append(row)
                except Exception:
                    # Skip problematic results
                    continue
                
            self.details.append(f"╚{'═' * (name_width+value_width+spec_width+12)}╝")
            
        except Exception:
            # Fallback to simple display if formatting fails
            self.details.append("║ Error formatting results table                                                        ║")
            self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
        
    def clear_results(self) -> None:
        """Clear all results and reset the UI."""
        logger.debug("Clearing results")
        self.table.setRowCount(0)
        self.details.clear()
        self.results = []
        self.metadata = {}
        self.current_file = None
        
    def export_to_csv(self) -> None:
        """Export current results to a CSV file."""
        if not self.results:
            logger.warning("No results to export")
            return
            
        try:
            if not self.current_file or not is_valid_path(self.current_file):
                logger.warning("No valid file path")
                return
            file_name = os.path.basename(self.current_file)
            base_name = os.path.splitext(file_name)[0]
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Results",
                base_name + "_results.csv",
                "CSV Files (*.csv)"
            )
            
            if save_path:
                save_to_csv(self.results, self.metadata, save_path)
                logger.debug("Results exported to: %s", save_path)
        except Exception as e:
            logger.error("Error exporting results: %s", str(e), exc_info=True)
            raise

def main():
    """Run the COA Analyzer application."""
    logger.debug("Starting application")
    try:
        app = QApplication(sys.argv)
        window = COAAnalyzer()
        window.show()
        logger.debug("Application started successfully")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 