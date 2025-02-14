import sys
import pandas as pd
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTableWidget, QTableWidgetItem, QComboBox
from PySide6.QtCore import Qt
import json

class ExcelLabelingGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Labeling Tool")
        self.setGeometry(300, 300, 1000, 700)

        layout = QVBoxLayout()

        self.label = QLabel("Select an Excel file to label:")
        layout.addWidget(self.label)

        self.select_button = QPushButton("Select Excel File")
        self.select_button.clicked.connect(self.select_excel_file)
        layout.addWidget(self.select_button)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.label_connector_button = QPushButton("Label Connector Name")
        self.label_connector_button.clicked.connect(self.label_connector_name)
        layout.addWidget(self.label_connector_button)

        self.label_pin_button = QPushButton("Label Pin Numbers")
        self.label_pin_button.clicked.connect(self.label_pin_numbers)
        layout.addWidget(self.label_pin_button)

        self.label_connection_button = QPushButton("Label Connections")
        self.label_connection_button.clicked.connect(self.label_connections)
        layout.addWidget(self.label_connection_button)

        self.save_button = QPushButton("Save Labels")
        self.save_button.clicked.connect(self.save_labels)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.file_path = ""
        self.labels = []
        self.current_label_type = None  # "Connector", "Pin", "Connection"
        self.cell_selection = []

    def select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.file_path = file_path
            self.load_excel(file_path)

    def load_excel(self, file_path):
        data = pd.read_excel(file_path, header=None)
        rows, cols = data.shape

        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)

        for row in range(rows):
            for col in range(cols):
                item = QTableWidgetItem(str(data.iloc[row, col]))
                self.table.setItem(row, col, item)

    def label_connector_name(self):
        self.current_label_type = "Connector"
        self.status_label("Select cells that are connector names.")
    
    def label_pin_numbers(self):
        self.current_label_type = "Pin"
        self.status_label("Select cells that are pin numbers.")
    
    def label_connections(self):
        self.current_label_type = "Connection"
        self.status_label("Select pairs of cells that represent connections.")

    def status_label(self, status_text):
        self.label.setText(status_text)
        self.cell_selection = []  # Clear previous selections

    def mousePressEvent(self, event):
        if self.current_label_type:
            row = self.table.rowAt(event.pos().y())
            col = self.table.columnAt(event.pos().x())

            if row >= 0 and col >= 0:
                cell_value = self.table.item(row, col).text()

                if (row, col) not in self.cell_selection:
                    self.cell_selection.append((row, col))

                    # Highlight selected cells
                    item = self.table.item(row, col)
                    item.setBackground(Qt.yellow)

                    self.status_label(f"Selected {self.current_label_type}: {cell_value} at Row {row+1}, Column {col+1}")

    def save_labels(self):
        labeled_data = []

        for row, col in self.cell_selection:
            cell_value = self.table.item(row, col).text()
            labeled_data.append({"row": row, "col": col, "label": self.current_label_type, "value": cell_value})

        with open('labeled_data.json', 'w') as f:
            json.dump(labeled_data, f)

        self.status_label("Labels saved!")
        self.cell_selection = []  # Clear after saving

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelLabelingGUI()
    window.show()
    sys.exit(app.exec())
