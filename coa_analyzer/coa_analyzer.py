import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                           QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from coa_analyzer.coa_extract import extract_coa_data, extract_metadata, read_input_file, save_to_csv

class COAAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COA Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create drag and drop area
        self.drop_area = QLabel("Drag and drop PDF files here")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
                font-size: 16px;
            }
        """)
        self.drop_area.setMinimumHeight(100)
        layout.addWidget(self.drop_area)
        
        # Create results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "File Name", "Material", "Batch", "Tests", "Pass", "Fail"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Create detailed results area
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        layout.addWidget(self.details)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)
        
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initialize results storage
        self.results = []
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            if file.lower().endswith('.pdf'):
                self.process_file(file)
                
    def process_file(self, file_path):
        try:
            # Process the file using our existing code
            coa_text = read_input_file(file_path)
            if not coa_text.strip():
                self.details.append(f"No COA data found in {os.path.basename(file_path)}")
                return
                
            # Extract data
            results = extract_coa_data(coa_text)
            metadata = extract_metadata(coa_text)
            
            # Add to results list
            self.results.append((file_path, results, metadata))
            
            # Update table
            self.update_table()
            
            # Show detailed results
            self.show_details(file_path, results, metadata)
            
        except Exception as e:
            self.details.append(f"Error processing {os.path.basename(file_path)}: {str(e)}")
            
    def update_table(self):
        self.table.setRowCount(len(self.results))
        for i, (file_path, results, metadata) in enumerate(self.results):
            # Get just the filename without path
            base_filename = os.path.basename(file_path)
            
            # Count results
            passes = sum(1 for r in results if r.result == "PASS")
            fails = sum(1 for r in results if r.result == "FAIL")
            
            # Get metadata
            material = metadata.get("Material", "").split()[0] if metadata.get("Material") else "N/A"
            batch = metadata.get("Batch", "N/A")
            
            # Add items to table
            self.table.setItem(i, 0, QTableWidgetItem(base_filename))
            self.table.setItem(i, 1, QTableWidgetItem(material))
            self.table.setItem(i, 2, QTableWidgetItem(batch))
            self.table.setItem(i, 3, QTableWidgetItem(str(len(results))))
            self.table.setItem(i, 4, QTableWidgetItem(str(passes)))
            self.table.setItem(i, 5, QTableWidgetItem(str(fails)))
            
    def show_details(self, file_path, results, metadata):
        # Clear previous content
        self.details.clear()
        
        # File header with separator
        self.details.append(f"╔{'═' * 78}╗")
        self.details.append(f"║ {'Results for ' + os.path.basename(file_path):<76} ║")
        self.details.append(f"╚{'═' * 78}╝")
        
        # Metadata section
        self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
        self.details.append("║ Metadata                                                                              ║")
        self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Calculate max key length for alignment
        max_key_len = max(len(key) for key in metadata.keys()) if metadata else 0
        
        for key, value in metadata.items():
            self.details.append(f"║ {key:<{max_key_len}} : {value:<{76-max_key_len-3}} ║")
        self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
        
        # Test results section
        self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
        self.details.append("║ Test Results                                                                          ║")
        self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Filter out non-test entries and duplicates
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
        
        # Calculate column widths based on filtered results
        name_width = max(len(str(r.name)) for r in filtered_results) if filtered_results else 20
        value_width = max(len(str(r.value)) for r in filtered_results) if filtered_results else 10
        spec_width = max(len(str(r.specification)) for r in filtered_results) if filtered_results else 20
        name_width = max(name_width, 20)  # Ensure minimum width
        value_width = max(value_width, 10)
        spec_width = max(spec_width, 20)
        
        # Header row
        header = f"║ {'Test Name':<{name_width}} │ {'Value':<{value_width}} │ {'Specification':<{spec_width}} │ {'Result':<10} ║"
        self.details.append(header)
        self.details.append("╠" + "═" * (name_width + 2) + "╪" + "═" * (value_width + 2) + "╪" + 
                          "═" * (spec_width + 2) + "╪" + "═" * 12 + "╣")
        
        # Data rows
        for result in filtered_results:
            row = f"║ {result.name:<{name_width}} │ {result.value:<{value_width}} │ {result.specification:<{spec_width}} │ {result.result:<10} ║"
            self.details.append(row)
        self.details.append("╚" + "═" * (name_width + 2) + "╧" + "═" * (value_width + 2) + "╧" + 
                          "═" * (spec_width + 2) + "╧" + "═" * 12 + "╝")
        
        # Summary section
        passes = sum(1 for r in filtered_results if r.result == "PASS")
        fails = sum(1 for r in filtered_results if r.result == "FAIL")
        unknowns = sum(1 for r in filtered_results if r.result == "UNKNOWN")
        
        self.details.append("\n╔══════════════════════════════════════════════════════════════════════════════════════╗")
        self.details.append("║ Summary                                                                               ║")
        self.details.append("╠══════════════════════════════════════════════════════════════════════════════════════╣")
        self.details.append(f"║ Total Tests: {len(filtered_results):<66} ║")
        self.details.append(f"║ PASS: {passes:<71} ║")
        self.details.append(f"║ FAIL: {fails:<71} ║")
        self.details.append(f"║ UNKNOWN: {unknowns:<68} ║")
        self.details.append("╚══════════════════════════════════════════════════════════════════════════════════════╝")
        
        # Add some spacing at the end
        self.details.append("\n" * 2)
        
    def clear_results(self):
        self.results = []
        self.table.setRowCount(0)
        self.details.clear()
        
    def export_to_csv(self):
        if not self.results:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Create a combined CSV with all results
                with open(file_path, 'w', newline='') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['File Name', 'Material', 'Batch', 'Tests', 'Pass', 'Fail'])
                    
                    # Write data
                    for file_path, results, metadata in self.results:
                        base_filename = os.path.basename(file_path)
                        passes = sum(1 for r in results if r.result == "PASS")
                        fails = sum(1 for r in results if r.result == "FAIL")
                        material = metadata.get("Material", "").split()[0] if metadata.get("Material") else "N/A"
                        batch = metadata.get("Batch", "N/A")
                        
                        writer.writerow([
                            base_filename,
                            material,
                            batch,
                            len(results),
                            passes,
                            fails
                        ])
                        
                self.details.append(f"\nResults exported to {file_path}")
                
            except Exception as e:
                self.details.append(f"Error exporting to CSV: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = COAAnalyzer()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 