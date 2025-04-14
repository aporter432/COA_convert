"""COA Analyzer GUI module for analyzing Certificate of Analysis documents."""

import sys
import os
import logging
import traceback
import gc
import psutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                           QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from coa_analyzer.coa_extract import extract_coa_data, extract_metadata, read_input_file, save_to_csv
from typing import cast, TypeGuard
import PyPDF2

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

# Set up crash logger
crash_logger = logging.getLogger("coa_analyzer.crash")
crash_handler = logging.FileHandler('coa_crash.log', mode='a')
crash_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
crash_logger.addHandler(crash_handler)
crash_logger.setLevel(logging.ERROR)

def is_valid_path(path: str | None) -> TypeGuard[str]:
    return isinstance(path, str) and bool(path)

def log_memory_usage(prefix=""):
    """Log current memory usage."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        memory_mb = mem_info.rss / 1024 / 1024
        logger.debug(f"{prefix} Memory usage: {memory_mb:.2f} MB")
        return memory_mb
    except Exception as e:
        logger.error(f"Error logging memory usage: {str(e)}")
        return 0

# Global exception handler
def global_exception_handler(exctype, value, tb):
    """Global exception handler to catch and log unhandled exceptions."""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    crash_logger.critical(f"UNHANDLED EXCEPTION: {error_msg}")
    # Log memory usage at crash time
    log_memory_usage("At crash:")
    # Call the original exception handler
    sys.__excepthook__(exctype, value, tb)

# Install the global exception handler
sys.excepthook = global_exception_handler

class COAAnalyzer(QMainWindow):
    """Main window class for the COA Analyzer application.
    
    This class provides a GUI interface for analyzing Certificate of Analysis (COA) 
    documents. It supports drag-and-drop functionality for PDF files and displays 
    results in both table and detailed text formats.
    """
    
    def __init__(self):
        super().__init__()
        
        # Set up a dedicated logger for GUI operations
        self.gui_logger = logging.getLogger("coa_analyzer.gui")
        gui_handler = logging.FileHandler('coa_gui.log', mode='w')
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.gui_logger.addHandler(gui_handler)
        self.gui_logger.setLevel(logging.DEBUG)
        self.gui_logger.info("GUI initialization started")
        
        # Initialize instance variables
        self.results: list = []
        self.metadata: dict = {}
        self.current_file: str | None = None
        self.is_processing: bool = False  # Flag to track if processing is in progress
        
        # Set up memory monitoring
        self.base_memory_usage = log_memory_usage("Base")
        
        # Set up periodic memory logging
        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self.log_periodic_memory)
        self.memory_timer.start(30000)  # Log every 30 seconds
        
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
        
        # Create buttons layout
        button_layout = QHBoxLayout()
        
        # Create Clear Results button with error handling
        try:
            self.clear_button = QPushButton("Clear Results")
            self.clear_button.clicked.connect(self._on_clear_button_clicked)
            button_layout.addWidget(self.clear_button)
            
            # Create Export to CSV button
            self.export_button = QPushButton("Export to CSV")
            self.export_button.clicked.connect(self._on_export_button_clicked)
            button_layout.addWidget(self.export_button)
            
            # Add button layout to main layout
            layout.addLayout(button_layout)
            logger.debug("Button initialization successful")
            self.gui_logger.info("Buttons initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing buttons: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.gui_logger.error(error_msg, exc_info=True)
            # Create a simpler fallback UI if button init fails
            try:
                fallback_label = QLabel("Button initialization failed. Use File menu instead.")
                layout.addWidget(fallback_label)
            except:
                pass
        
        # Set up drag and drop
        self.setAcceptDrops(True)
        
        self.gui_logger.info("COAAnalyzer initialization complete")
        logger.debug("COAAnalyzer initialization complete")
    
    def log_periodic_memory(self):
        """Periodically log memory usage for monitoring."""
        try:
            current_memory = log_memory_usage("Periodic")
            memory_change = current_memory - self.base_memory_usage
            self.gui_logger.debug(f"Memory change since startup: {memory_change:.2f} MB")
        except Exception as e:
            self.gui_logger.error(f"Error in periodic memory logging: {str(e)}", exc_info=True)
        
    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        if event is None:
            self.gui_logger.error("dragEnterEvent received None event")
            return
        mime_data = event.mimeData()
        if mime_data is None:
            self.gui_logger.error("dragEnterEvent received None mimeData")
            event.ignore()
            return
        if mime_data.hasUrls():
            self.gui_logger.debug("dragEnterEvent accepting drop with URLs")
            event.acceptProposedAction()
        else:
            self.gui_logger.debug("dragEnterEvent ignoring drop without URLs")
            event.ignore()

    def dropEvent(self, event: QDropEvent | None) -> None:
        if event is None:
            self.gui_logger.error("dropEvent received None event")
            return
        
        # Check if already processing to prevent concurrent operations
        if self.is_processing:
            self.gui_logger.warning("Drop event ignored - already processing files")
            self.details.setText("Still processing previous file. Please wait...")
            event.ignore()
            return
        
        self.gui_logger.debug("Drop event received")
        self.is_processing = True  # Set processing flag
        
        try:
            mime_data = event.mimeData()
            if mime_data is None:
                self.gui_logger.error("dropEvent received None mimeData")
                event.ignore()
                self.is_processing = False
                return
                
            self.gui_logger.debug(f"Drop contains {len(mime_data.urls())} URLs")
            
            # Disable buttons during processing
            if hasattr(self, 'clear_button'):
                self.clear_button.setEnabled(False)
            if hasattr(self, 'export_button'):
                self.export_button.setEnabled(False)
            
            # Process files one by one
            file_count = len(mime_data.urls())
            for i, url in enumerate(mime_data.urls()):
                file_path = url.toLocalFile()
                self.gui_logger.debug(f"Processing dropped file {i+1} of {file_count}: {file_path}")
                
                if file_path and file_path.lower().endswith('.pdf'):
                    try:
                        self.details.setText(f"Processing {os.path.basename(file_path)}... ({i+1}/{file_count})")
                        QApplication.processEvents()  # Update UI to show processing message
                        
                        # Process the file with specific error handling
                        self.process_file(file_path)
                        
                        # Force cleanup between files if processing multiple files
                        if file_count > 1:
                            self.gui_logger.debug(f"Cleaning up after file {i+1} before processing next file")
                            self.reset_memory()
                            
                    except Exception as e:
                        error_details = traceback.format_exc()
                        self.gui_logger.error(f"Error processing file: {str(e)}\n{error_details}")
                        logger.error(f"Error processing file: {e}", exc_info=True)
                        self.details.setText(f"Error: {str(e)}")
                        
                        # Log memory at point of error
                        log_memory_usage(f"Error processing {os.path.basename(file_path)}:")
                        
                        # Cleanup after error
                        self.reset_memory()
                else:
                    self.gui_logger.warning(f"Dropped file is not a PDF: {file_path}")
                    self.details.setText(f"Warning: {os.path.basename(file_path)} is not a PDF file.")
            
            # Re-enable buttons after processing
            if hasattr(self, 'clear_button'):
                self.clear_button.setEnabled(True)
            if hasattr(self, 'export_button'):
                self.export_button.setEnabled(True)
                
            self.gui_logger.debug("Drop event processing complete")
            event.acceptProposedAction()
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Unhandled exception in dropEvent: {str(e)}\n{error_details}")
            logger.error(f"Unhandled exception in dropEvent: {str(e)}", exc_info=True)
            try:
                self.details.setText(f"Error: {str(e)}")
                event.acceptProposedAction()
            except:
                pass
        finally:
            # Always reset processing flag and re-enable buttons
            self.is_processing = False
            if hasattr(self, 'clear_button'):
                self.clear_button.setEnabled(True)
            if hasattr(self, 'export_button'):
                self.export_button.setEnabled(True)
            
            # Force garbage collection
            self.reset_memory()
            log_memory_usage("After drop event:")

    def process_file(self, file_path: str) -> None:
        """Process a COA file and display results."""
        raw_text = None
        try:
            # Log start of processing with memory usage
            self.gui_logger.info(f"Starting to process file: {file_path}")
            log_memory_usage("Before processing:")
            
            # Force garbage collection before processing a new file
            self.reset_memory()
            
            if not is_valid_path(file_path):
                self.details.setText("Error: Invalid file path")
                logger.error(f"Invalid file path: {file_path}")
                return
            
            # Check file size first
            try:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                logger.debug(f"File size: {file_size:.2f} MB")
                if file_size > 20:  # Warn for files larger than 20MB
                    logger.warning(f"Large file detected: {file_size:.2f} MB. This may cause performance issues.")
                    self.details.setText(f"Warning: Large file ({file_size:.2f} MB). Processing may take longer...")
                    QApplication.processEvents()  # Update UI
            except Exception as e:
                logger.error(f"Error checking file size: {str(e)}")
                
            logger.debug(f"Processing file: {file_path}")
            
            # Process file in stages with explicit error handling for each stage
            # Stage 1: Read input file
            try:
                self.gui_logger.debug("Stage 1: Reading input file")
                raw_text = read_input_file(file_path)
                logger.debug(f"Text extraction complete, length: {len(raw_text) if raw_text else 0}")
                log_memory_usage("After text extraction:")
                
                if not raw_text:
                    self.details.setText("Could not read file")
                    logger.error(f"No text extracted from file: {file_path}")
                    return
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Exception during read_input_file: {str(e)}\n{error_details}")
                self.gui_logger.error(f"Stage 1 failure: {str(e)}\n{error_details}")
                self.details.setText(f"Error reading file: {str(e)}")
                return
            
            # Stage 2: Extract COA data
            results = None
            try:
                self.gui_logger.debug("Stage 2: Extracting COA data")
                results = extract_coa_data(raw_text)
                logger.debug(f"Data extraction complete, results count: {len(results)}")
                
                # Cleanup after data extraction
                # We keep raw_text for metadata extraction, but we can do a GC pass
                gc.collect()
                log_memory_usage("After data extraction:")
                
                if not results:
                    self.details.setText("No COA data found")
                    logger.error(f"No COA data found in: {file_path}")
                    # Aggressive cleanup
                    raw_text = None
                    self.reset_memory()
                    return
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Exception during extract_coa_data: {str(e)}\n{error_details}")
                self.gui_logger.error(f"Stage 2 failure: {str(e)}\n{error_details}")
                self.details.setText(f"Error extracting data: {str(e)}")
                # Aggressive cleanup
                raw_text = None
                self.reset_memory()
                return
            
            # Stage 3: Extract metadata
            metadata = None    
            try:
                self.gui_logger.debug("Stage 3: Extracting metadata")
                metadata = extract_metadata(raw_text)
                logger.debug(f"Metadata extraction complete: {metadata}")
                # Done with raw text now, release it
                raw_text = None
                # Aggressive cleanup
                self.reset_memory()
                log_memory_usage("After metadata extraction:")
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Exception during extract_metadata: {str(e)}\n{error_details}")
                self.gui_logger.error(f"Stage 3 failure: {str(e)}\n{error_details}")
                self.details.setText(f"Error extracting metadata: {str(e)}")
                # Aggressive cleanup
                raw_text = None
                self.reset_memory()
                return
            
            # Stage 4: Update UI
            try:
                self.gui_logger.debug("Stage 4: Updating UI")
                self.results = results
                self.metadata = metadata
                self.current_file = file_path
                
                # Update UI in smaller stages to avoid blocking
                self.update_table()
                log_memory_usage("After table update:")
                
                self.show_details(file_path, results, metadata)
                log_memory_usage("After details update:")
                
                logger.debug("UI updated successfully")
                self.gui_logger.info(f"Successfully processed file: {file_path}")
                
                # Force garbage collection after processing
                gc.collect()
                log_memory_usage("After complete processing:")
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Exception during UI update: {str(e)}\n{error_details}")
                self.gui_logger.error(f"Stage 4 failure: {str(e)}\n{error_details}")
                self.details.setText(f"Error updating UI: {str(e)}")
                
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"Unhandled exception in process_file: {str(e)}\n{error_details}")
            self.gui_logger.error(f"Unhandled exception in process_file: {str(e)}\n{error_details}")
            crash_logger.error(f"CRASH in process_file: {str(e)}\n{error_details}")
            self.details.setText(f"Error: {str(e)}")
            # Clean up in case of crash
            self.results = []
            self.metadata = {}
            raw_text = None
        finally:
            # Final cleanup, regardless of success or failure
            if raw_text is not None:
                raw_text = None
            self.reset_memory()
            log_memory_usage("Final memory usage:")

    def update_table(self) -> None:
        """Update the results table with current data."""
        try:
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
            
            # Process UI events to prevent freezing
            QApplication.processEvents()
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Error updating table: {str(e)}\n{error_details}")
            logger.error(f"Error updating table: {str(e)}\n{error_details}")
            
    def show_details(self, file_path: str, results: list, metadata: dict) -> None:
        """Display detailed results in the text area.
        
        Args:
            file_path: Path to the processed file
            results: List of test results
            metadata: Dictionary of metadata from the COA
        """
        try:
            logger.debug("Showing details")
            # Clear previous content
            self.details.clear()
            
            # File header with separator
            self.details.append(f"╔{'═' * 78}╗")
            self.details.append(f"║ {'Results for ' + os.path.basename(file_path):<76} ║")
            self.details.append(f"╚{'═' * 78}╝")
            
            # Process UI events to prevent freezing
            QApplication.processEvents()
            
            self._show_metadata_section(metadata)
            QApplication.processEvents()
            
            self._show_results_section(results)
            QApplication.processEvents()
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Error showing details: {str(e)}\n{error_details}")
            logger.error(f"Error showing details: {str(e)}\n{error_details}")
            self.details.setText(f"Error displaying results: {str(e)}")
        
    def _show_metadata_section(self, metadata: dict) -> None:
        """Display the metadata section in the details area.
        
        Args:
            metadata: Dictionary of metadata from the COA
        """
        try:
            self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
            self.details.append("║ Metadata                                                                              ║")
            self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
            
            # Calculate max key length for alignment
            max_key_len = max(len(key) for key in metadata.keys()) if metadata else 0
            
            for key, value in metadata.items():
                self.details.append(f"║ {key:<{max_key_len}} : {value:<{76-max_key_len-3}} ║")
            self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
            
            # Process UI events to prevent freezing
            QApplication.processEvents()
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Error showing metadata: {str(e)}\n{error_details}")
            self.details.append("Error displaying metadata")
        
    def _show_results_section(self, results: list) -> None:
        """Display the test results section in the details area.
        
        Args:
            results: List of test results
        """
        try:
            self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
            self.details.append("║ Test Results                                                                          ║")
            self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
            
            # Process UI events to prevent freezing
            QApplication.processEvents()
            
            # Filter out non-test entries and duplicates
            filtered_results = self._filter_results(results)
            
            # Calculate column widths
            name_width, value_width, spec_width = self._calculate_column_widths(filtered_results)
            
            # Display results
            self._display_results_table(filtered_results, name_width, value_width, spec_width)
            
            # Process UI events to prevent freezing
            QApplication.processEvents()
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Error showing results section: {str(e)}\n{error_details}")
            self.details.append("Error displaying test results")
        
    def _filter_results(self, results: list) -> list:
        """Filter out non-test entries and duplicates from results.
        
        Args:
            results: List of test results
            
        Returns:
            List of filtered test results
        """
        try:
            seen_tests = set()
            filtered_results = []
            
            for result in results:
                if not result:
                    continue
                    
                # Skip non-test entries
                if hasattr(result, 'name') and result.name in ["DATE OF PRODUCTION", "COUNTRY OF ORIGIN"]:
                    continue
                    
                # Skip entries without values or specifications
                if not getattr(result, 'value', None) or not getattr(result, 'specification', None):
                    continue
                    
                # Create a unique key for this test
                test_key = f"{getattr(result, 'name', 'unknown')}_{getattr(result, 'method', 'unknown')}_{getattr(result, 'value', 'unknown')}_{getattr(result, 'specification', 'unknown')}"
                if test_key not in seen_tests:
                    seen_tests.add(test_key)
                    filtered_results.append(result)
                    
            return filtered_results
        except Exception as e:
            self.gui_logger.error(f"Error filtering results: {str(e)}", exc_info=True)
            return []
        
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
            name_width = max((len(str(getattr(r, 'name', ''))) for r in results if hasattr(r, 'name') and r.name is not None), default=20)
            value_width = max((len(str(getattr(r, 'value', ''))) for r in results if hasattr(r, 'value') and r.value is not None), default=10)
            spec_width = max((len(str(getattr(r, 'specification', ''))) for r in results if hasattr(r, 'specification') and r.specification is not None), default=20)
            
            return (
                max(name_width, 20),  # Ensure minimum width
                max(value_width, 10),
                max(spec_width, 20)
            )
        except Exception as e:
            self.gui_logger.error(f"Error calculating column widths: {str(e)}", exc_info=True)
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
            
            # Process small batches to avoid UI freezing
            batch_size = 10
            for i in range(0, len(results), batch_size):
                batch = results[i:i+batch_size]
                
                # Results
                for result in batch:
                    try:
                        # Safely get values with fallbacks
                        name = str(getattr(result, 'name', 'N/A')) if hasattr(result, 'name') and result.name is not None else "N/A"
                        value = str(getattr(result, 'value', 'N/A')) if hasattr(result, 'value') and result.value is not None else "N/A"
                        spec = str(getattr(result, 'specification', 'N/A')) if hasattr(result, 'specification') and result.specification is not None else "N/A"
                        status = str(getattr(result, 'result', 'UNKNOWN')) if hasattr(result, 'result') and result.result is not None else "UNKNOWN"
                        
                        row = f"║ {name:<{name_width}} │ {value:<{value_width}} │ {spec:<{spec_width}} │ {status:<6} ║"
                        self.details.append(row)
                    except Exception as e:
                        self.gui_logger.error(f"Error formatting result row: {str(e)}", exc_info=True)
                        # Skip problematic results
                        continue
                
                # Process UI events after each batch
                QApplication.processEvents()
                
            self.details.append(f"╚{'═' * (name_width+value_width+spec_width+12)}╝")
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.gui_logger.error(f"Error displaying results table: {str(e)}\n{error_details}")
            # Fallback to simple display if formatting fails
            self.details.append("║ Error formatting results table                                                        ║")
            self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
        
    def _on_clear_button_clicked(self):
        """Safe wrapper for clear_results that logs all activities"""
        self.gui_logger.info("Clear button clicked")
        try:
            # Disable button while operation is in progress
            self.clear_button.setEnabled(False)
            self.details.setText("Clearing results...")
            
            # Force Qt to process the events to update UI
            QApplication.processEvents()
            
            # Clear all data and UI
            self.clear_results()
            
            # Additional cleanup to ensure all memory is released
            self.reset_memory()
            
            # Show cleared message
            self.details.setText("All results cleared successfully")
            self.gui_logger.info("Clear operation completed successfully")
        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"Error during clear operation: {str(e)}"
            self.gui_logger.error(f"{error_msg}\n{error_details}")
            crash_logger.error(f"CRASH in clear operation: {str(e)}\n{error_details}")
            try:
                self.details.setText(f"Error clearing results: {str(e)}")
            except:
                pass
        finally:
            # Re-enable button
            try:
                self.clear_button.setEnabled(True)
            except:
                pass
            # Force garbage collection
            gc.collect()
            log_memory_usage("After clear:")

    def _on_export_button_clicked(self):
        """Safe wrapper for export_to_csv that logs all activities"""
        self.gui_logger.info("Export button clicked")
        try:
            # Disable button while operation is in progress
            self.export_button.setEnabled(False)
            
            # Force Qt to process the events to update UI
            QApplication.processEvents()
            
            self.export_to_csv()
            self.gui_logger.info("Export operation completed or canceled by user")
        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"Error during export operation: {str(e)}"
            self.gui_logger.error(f"{error_msg}\n{error_details}")
            crash_logger.error(f"CRASH in export operation: {str(e)}\n{error_details}")
            try:
                self.details.setText(f"Error exporting results: {str(e)}")
            except:
                pass
        finally:
            # Re-enable button
            try:
                self.export_button.setEnabled(True)
            except:
                pass
            # Force garbage collection
            gc.collect()

    def reset_memory(self):
        """Force aggressive memory cleanup to reclaim memory after processing."""
        try:
            self.gui_logger.debug("Starting aggressive memory cleanup")
            
            # Clear all cached data explicitly
            if hasattr(self, 'raw_text') and self.raw_text is not None:
                self.raw_text = None
            
            # Clear large data structures
            self.results = []
            self.metadata = {}
            if self.current_file:
                self.current_file = None
            
            # Close any open file handles
            try:
                for obj in gc.get_objects():
                    try:
                        if isinstance(obj, PyPDF2.PdfReader):
                            # PdfReader has a stream attribute that can be closed
                            if hasattr(obj, 'stream') and obj.stream:
                                obj.stream.close()
                        elif isinstance(obj, PyPDF2.PdfWriter):
                            # PdfWriter doesn't have a direct stream to close
                            pass
                    except:
                        pass
            except:
                pass
            
            # Force multiple garbage collection cycles
            for _ in range(3):
                gc.collect()
            
            # Log memory after cleanup
            mem_usage = log_memory_usage("After memory reset:")
            self.gui_logger.debug(f"Memory reset complete: {mem_usage:.2f} MB")
            
            return mem_usage
        except Exception as e:
            self.gui_logger.error(f"Error during memory reset: {str(e)}", exc_info=True)
            return 0

    def clear_results(self) -> None:
        """Clear all results and reset the UI."""
        try:
            self.gui_logger.debug("Starting clear_results")
            logger.debug("Clearing results")
            
            # Clear UI elements first
            if self.table is not None:
                self.gui_logger.debug("Clearing table")
                self.table.setRowCount(0)
            else:
                self.gui_logger.warning("Table is None during clear_results")
                
            if self.details is not None:
                self.gui_logger.debug("Clearing details")
                self.details.clear()
            else:
                self.gui_logger.warning("Details is None during clear_results")
            
            # Process events to update UI
            QApplication.processEvents()
            
            self.gui_logger.debug("Clearing data structures")
            
            # Clear all large data structures
            if hasattr(self, 'raw_text') and self.raw_text is not None:
                self.raw_text = None
            
            # Explicitly clear all lists and dicts to help garbage collector
            if self.results:
                for result in self.results:
                    # Clear any large attributes in TestResult objects
                    if hasattr(result, '__dict__'):
                        result.__dict__.clear()
                        
                self.results.clear()
                self.results = []
                
            if self.metadata:
                self.metadata.clear()
                self.metadata = {}
                
            self.current_file = None
            
            # Force garbage collection multiple times
            for _ in range(2):
                gc.collect()
            
            log_memory_usage("After clearing structures:")
            
            self.gui_logger.debug("Results cleared successfully")
            logger.debug("Results cleared successfully")
            
            # Final aggressive memory cleanup
            self.reset_memory()
        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"Error clearing results: {str(e)}"
            logger.error(f"{error_msg}\n{error_details}")
            self.gui_logger.error(f"{error_msg}\n{error_details}")
            crash_logger.error(f"CRASH in clear_results: {str(e)}\n{error_details}")
            # Don't try to use UI if that's what's failing
            try:
                if self.details is not None:
                    self.details.setText(f"Error clearing results: {str(e)}")
            except:
                pass

    def export_to_csv(self) -> None:
        """Export current results to a CSV file."""
        try:
            self.gui_logger.debug("Starting export_to_csv")
            if not self.results:
                msg = "No results to export"
                logger.warning(msg)
                self.gui_logger.warning(msg)
                self.details.setText("No results available to export")
                return
                
            if not self.current_file or not is_valid_path(self.current_file):
                msg = "No valid file path for export"
                logger.warning(msg)
                self.gui_logger.warning(msg)
                self.details.setText("Cannot export: no valid source file")
                return
                
            file_name = os.path.basename(self.current_file)
            base_name = os.path.splitext(file_name)[0]
            
            self.gui_logger.debug("Opening file save dialog")
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Results",
                base_name + "_results.csv",
                "CSV Files (*.csv)"
            )
            
            if save_path:
                try:
                    self.gui_logger.debug(f"Saving to: {save_path}")
                    save_to_csv(self.results, self.metadata, save_path)
                    logger.debug(f"Results exported to: {save_path}")
                    self.gui_logger.info(f"Results exported to: {save_path}")
                    self.details.setText(f"Results exported to: {save_path}")
                except Exception as e:
                    error_details = traceback.format_exc()
                    error_msg = f"Error saving CSV file: {str(e)}"
                    logger.error(f"{error_msg}\n{error_details}")
                    self.gui_logger.error(f"{error_msg}\n{error_details}")
                    self.details.setText(error_msg)
            else:
                self.gui_logger.debug("CSV export cancelled by user")
                logger.debug("CSV export cancelled by user")
        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"Error during export operation: {str(e)}"
            logger.error(f"{error_msg}\n{error_details}")
            self.gui_logger.error(f"{error_msg}\n{error_details}")
            crash_logger.error(f"CRASH in export_to_csv: {str(e)}\n{error_details}")
            self.details.setText(error_msg)
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Log final memory usage
        self.gui_logger.info("Application closing")
        log_memory_usage("Final memory at close:")
        # Call parent method
        super().closeEvent(event)

def main():
    """Run the COA Analyzer application."""
    logger.debug("Starting application")
    try:
        # Log startup memory
        log_memory_usage("Application startup:")
        
        app = QApplication(sys.argv)
        window = COAAnalyzer()
        window.show()
        logger.debug("Application started successfully")
        sys.exit(app.exec())
    except Exception as e:
        error_details = traceback.format_exc()
        logger.critical(f"Fatal application error: {str(e)}\n{error_details}")
        crash_logger.critical(f"FATAL ERROR: {str(e)}\n{error_details}")
        print(f"Fatal error: {str(e)}")
        # Create fallback error dialog if possible
        try:
            from PyQt6.QtWidgets import QMessageBox
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("COA Analyzer Error")
            error_dialog.setText("The application encountered a fatal error")
            error_dialog.setDetailedText(f"Error: {str(e)}\n\nPlease check coa_processing.log for details.")
            error_dialog.exec()
        except:
            # If even the error dialog fails, at least we tried
            pass
        sys.exit(1)

if __name__ == "__main__":
    main() 