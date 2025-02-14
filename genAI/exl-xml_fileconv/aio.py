import sys
import pandas as pd
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import xml.etree.ElementTree as ET

class ExcelLabelingGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Labeling Tool with Advanced Model Training")
        self.setGeometry(300, 300, 1000, 700)

        layout = QVBoxLayout()

        # Status Label
        self.label = QLabel("Select an Excel file to label:")
        layout.addWidget(self.label)

        # Buttons for file loading, labeling, training, and XML generation
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

        self.train_button = QPushButton("Start Training")
        self.train_button.clicked.connect(self.start_training)
        layout.addWidget(self.train_button)

        self.generate_xml_button = QPushButton("Generate XML")
        self.generate_xml_button.clicked.connect(self.generate_xml)
        layout.addWidget(self.generate_xml_button)

        self.setLayout(layout)

        self.file_path = ""
        self.data = None
        self.labels = []
        self.current_label_type = None  # "Connector", "Pin", "Connection"
        self.cell_selection = []

        # Model and data for training
        self.model = None
        self.feature_data = []
        self.label_data = []

    def select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            self.file_path = file_path
            self.load_excel(file_path)

    def load_excel(self, file_path):
        try:
            # Read the Excel file
            data = pd.read_excel(file_path, header=None)

            if data.empty:
                self.label.setText("Error: The Excel file is empty.")
                return

            # Print data for debugging
            print(f"Data Loaded from {file_path}")
            print(data.head())

            # Store data
            self.data = data

            # Set rows and columns in the table for display
            rows, cols = data.shape
            self.table.setRowCount(rows)
            self.table.setColumnCount(cols)

            for row in range(rows):
                for col in range(cols):
                    item = QTableWidgetItem(str(data.iloc[row, col]))
                    self.table.setItem(row, col, item)

            self.label.setText("Excel data loaded. Start labeling!")

        except Exception as e:
            print(f"Error loading Excel file: {e}")
            self.label.setText("Error loading the Excel file.")

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
                    item = self.table.item(row, col)
                    item.setBackground(Qt.yellow)

                    self.status_label(f"Selected {self.current_label_type}: {cell_value}")

    def save_labels(self):
        # Here, we would collect and save all labeled data into a dictionary
        self.labels = [{"type": self.current_label_type, "coordinates": self.cell_selection}]
        print(f"Labeled Data: {self.labels}")

    def extract_features(self):
        # Assuming the data is a connector list with multiple pins
        feature_data = []
        label_data = []

        for row in self.data.iterrows():
            connector_name = row[1][0]  # Let's assume the first column is connector name
            pin_data = row[1][1:].dropna()  # All other columns are pins

            # Features could include: length of pin list, connector type (encoded), number of connections
            num_pins = len(pin_data)
            num_connections = pin_data.count()  # For simplicity, count non-empty pins as "connections"

            features = [num_pins, num_connections]  # Example feature extraction
            feature_data.append(features)
            label_data.append(connector_name)  # Let's use the connector name as the label for simplicity

        self.feature_data = feature_data
        self.label_data = label_data

    def start_training(self):
        if not self.data.empty:
            self.extract_features()

            # Split data for training (80% train, 20% test)
            X_train, X_test, y_train, y_test = train_test_split(self.feature_data, self.label_data, test_size=0.2, random_state=42)

            # Train a Gradient Boosting Model (you can try others like RandomForest or Neural Networks)
            self.model = GradientBoostingClassifier()
            self.model.fit(X_train, y_train)

            # Test the model accuracy
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model Accuracy: {accuracy * 100:.2f}%")

            self.label.setText(f"Model training completed! Accuracy: {accuracy * 100:.2f}%")

    def generate_xml(self):
        if self.model:
            # Create XML structure
            root = ET.Element("CableList")
            cable = ET.SubElement(root, "Cable", Name="TestCable")
            connectors = ET.SubElement(cable, "Connectors")

            # Using the model to generate predictions for each connector
            for i, features in enumerate(self.feature_data):
                prediction = self.model.predict([features])[0]

                connector = ET.SubElement(connectors, "Connector", Name=f"Connector_{i}", ConName=prediction, ConID=f"ID_{i}")
                pins = ET.SubElement(connector, "Pins")
                pins.text = str(len(features))  # Simulate number of pins

            from_to = ET.SubElement(cable, "FromTo")
            # Add dummy connections for now
            connection = ET.SubElement(from_to, "Cx", From="J1:1", To="J2:1", Type="Wire")

            # Save to XML file
            tree = ET.ElementTree(root)
            with open("output.xml", "wb") as file:
                tree.write(file)
            
            self.label.setText("XML file generated successfully!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelLabelingGUI()
    window.show()
    sys.exit(app.exec())
