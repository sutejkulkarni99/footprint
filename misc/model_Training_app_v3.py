import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt
import pandas as pd
import re
from collections import defaultdict

class ConnectorTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cable Connector Trainer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Data configuration
        self.cell_width = 120
        self.cell_height = 30
        
        # Data storage
        self.df = None
        self.selections = []
        self.pattern_db = defaultdict(list)
        
        # Initialize GUI
        self.initUI()
    
    def initUI(self):
        # Main layout
        layout = QVBoxLayout()
        
        # File selection controls
        self.load_button = QPushButton("Load Excel File")
        self.load_button.clicked.connect(self.load_file)
        layout.addWidget(self.load_button)
        
        # Table widget
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Control panel
        self.control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        # Connector name input
        self.connector_label = QLabel("Connector Name:")
        control_layout.addWidget(self.connector_label)
        
        self.connector_input = QLineEdit()
        control_layout.addWidget(self.connector_input)
        
        # Control buttons
        self.confirm_button = QPushButton("Confirm Selection")
        self.confirm_button.clicked.connect(self.save_selection)
        control_layout.addWidget(self.confirm_button)
        
        self.train_button = QPushButton("Train Model")
        self.train_button.clicked.connect(self.train_model)
        control_layout.addWidget(self.train_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        control_layout.addWidget(self.reset_button)
        
        self.control_panel.setLayout(control_layout)
        layout.addWidget(self.control_panel)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Set layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
        if file_path:
            self.df = pd.read_excel(file_path)
            self.draw_spreadsheet()
            self.status_label.setText(f"Loaded: {file_path}")
    
    def draw_spreadsheet(self):
        if self.df is None:
            return

        self.table.setRowCount(len(self.df))
        self.table.setColumnCount(len(self.df.columns))
        self.table.setHorizontalHeaderLabels(self.df.columns)
        
        for row_idx in range(len(self.df)):
            for col_idx in range(len(self.df.columns)):
                cell_value = str(self.df.iat[row_idx, col_idx])
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(cell_value))
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def save_selection(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges or not self.connector_input.text():
            QMessageBox.warning(self, "Input Error", "Please make a selection and enter a connector name!")
            return
        
        selected_range = selected_ranges[0]
        start_row = selected_range.topRow()
        end_row = selected_range.bottomRow()
        start_col = selected_range.leftColumn()
        end_col = selected_range.rightColumn()
        
        # Collect pin data
        pins = []
        for row_idx in range(start_row, end_row + 1):
            for col_idx in range(start_col, end_col + 1):
                pins.append(str(self.df.iat[row_idx, col_idx]))
        
        # Store selection
        self.selections.append({
            'connector': self.connector_input.text().strip(),
            'pins': pins,
            'location': (start_col, start_row, end_col, end_row)
        })
        
        # Clear inputs
        self.connector_input.clear()
        self.status_label.setText(f"Saved {len(pins)} pins for {self.selections[-1]['connector']}")
    
    def train_model(self):
        if not self.selections:
            QMessageBox.warning(self, "No Data", "Please make some selections first!")
            return
        
        # Analyze patterns in selected data
        pattern_counts = defaultdict(int)
        total_pins = 0
        
        for selection in self.selections:
            for pin in selection['pins']:
                # Find common connector-pin patterns
                matches = re.findall(r'\b([A-Z]+)\s*[-_]?\s*(\d+)\b', pin, re.IGNORECASE)
                for conn, pin_num in matches:
                    pattern = f"{conn.upper()}-{pin_num}"
                    pattern_counts[pattern] += 1
                    total_pins += 1
        
        # Calculate confidence scores
        self.pattern_db.clear()
        for pattern, count in pattern_counts.items():
            confidence = count / total_pins
            self.pattern_db[pattern] = confidence
        
        # Save training data to user-specified directory
        training_data = []
        for pattern, confidence in self.pattern_db.items():
            source, target = pattern.split('-')
            training_data.append({'Source': source, 'Target': target, 'Confidence': confidence})
        
        df_training = pd.DataFrame(training_data)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Training Data", "", "Excel Files (*.xlsx)")
        if save_path:
            df_training.to_excel(save_path, index=False)
            QMessageBox.information(self, "Training Complete", 
                              f"Learned {len(self.pattern_db)} patterns\n"
                              f"Average confidence: {sum(self.pattern_db.values())/len(self.pattern_db):.2f}")
    
    def reset(self):
        self.df = None
        self.selections = []
        self.pattern_db.clear()
        self.connector_input.clear()
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.status_label.setText("System reset - ready for new file")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConnectorTrainer()
    window.show()
    sys.exit(app.exec_())