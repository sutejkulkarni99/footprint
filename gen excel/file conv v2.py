import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
import pandas as pd
import os
from transformers import pipeline
import re
from collections import defaultdict

class CablePlanProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cable Plan Processor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize AI Model for pattern recognition
        self.nlp = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        
        # Data storage
        self.source_file = None
        self.connector_patterns = defaultdict(list)
        
        # Initialize GUI
        self.initUI()
    
    def initUI(self):
        # Main layout
        layout = QVBoxLayout()
        
        # File Selection Controls
        file_controls_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Source File")
        self.load_button.clicked.connect(self.load_file)
        file_controls_layout.addWidget(self.load_button)
        
        self.process_single_button = QPushButton("Process Single File")
        self.process_single_button.clicked.connect(self.process_single)
        file_controls_layout.addWidget(self.process_single_button)
        
        self.process_batch_button = QPushButton("Process Batch")
        self.process_batch_button.clicked.connect(self.process_batch)
        file_controls_layout.addWidget(self.process_batch_button)
        
        layout.addLayout(file_controls_layout)
        
        # Results Display
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Source Connector/Pin", "Destination Connector/Pin"])
        layout.addWidget(self.tree)
        
        # Status Bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Set layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Ask user to load training data
        self.load_training_data()
    
    def load_file(self):
        self.source_file, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xlsx)")
        if self.source_file:
            self.status_label.setText(f"Loaded: {os.path.basename(self.source_file)}")
            self.analyze_patterns(self.source_file)
    
    def load_training_data(self):
        """Ask user to load previously saved training data"""
        training_data_path, _ = QFileDialog.getOpenFileName(self, "Open Training Data File", "", "Excel Files (*.xlsx)")
        if training_data_path:
            df = pd.read_excel(training_data_path)
            for _, row in df.iterrows():
                source = row['Source']
                target = row['Target']
                self.connector_patterns[source].append(target)
            self.status_label.setText(f"Loaded training data with {len(self.connector_patterns)} patterns")
        else:
            self.status_label.setText("No training data found")
    
    def analyze_patterns(self, file_path):
        """Use AI to identify connection patterns in the data"""
        df = pd.read_excel(file_path)
        text_blocks = df.astype(str).agg(' '.join, axis=1).tolist()
        
        # AI-powered pattern recognition
        connections = []
        for text in text_blocks:
            entities = self.nlp(text)
            conn_entities = [e for e in entities if e['entity_group'] in ['CONN', 'PIN']]
            connections.extend(self.extract_connections(conn_entities))
        
        self.learn_connection_patterns(connections)
    
    def extract_connections(self, entities):
        """Convert AI-detected entities to connection pairs"""
        connections = []
        current_connector = None
        current_pin = None
        
        for entity in entities:
            text = entity['word']
            if entity['entity_group'] == 'CONN':
                current_connector = text
            elif entity['entity_group'] == 'PIN' and current_connector:
                if current_pin:
                    # Store completed connection
                    connections.append(f"{current_connector} {current_pin}")
                    current_pin = None
                current_pin = text
            elif current_connector and current_pin:
                # Handle multi-word entities
                current_pin += text
                
        return connections
    
    def learn_connection_patterns(self, connections):
        """Build connection mapping patterns"""
        for conn in connections:
            parts = re.split(r'\s+', conn)
            if len(parts) >= 4:
                source = f"{parts[0]} {parts[1]}"
                target = f"{parts[2]} {parts[3]}"
                self.connector_patterns[source].append(target)
        self.status_label.setText(f"Learned {len(self.connector_patterns)} connection patterns")
    
    def process_single(self):
        if self.source_file:
            output = self.process_file(self.source_file)
            self.display_results(output)
            self.save_output(output, self.source_file)
    
    def process_batch(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Open Excel Files", "", "Excel Files (*.xlsx)")
        for file in files:
            output = self.process_file(file)
            self.save_output(output, file)
    
    def process_file(self, file_path):
        """Process a file using learned patterns"""
        df = pd.read_excel(file_path)
        processed_data = []
        
        for _, row in df.iterrows():
            for cell in row:
                connections = self.parse_cell(str(cell))
                processed_data.extend(connections)
        
        return pd.DataFrame(processed_data, columns=["Source", "Destination"])
    
    def parse_cell(self, text):
        """Use AI and regex patterns to extract connections"""
        # First try learned patterns
        for pattern in self.connector_patterns:
            if pattern in text:
                return [(pattern, target) for target in self.connector_patterns[pattern]]
        
        # Fallback to AI parsing
        entities = self.nlp(text)
        return self.extract_connections(entities)
    
    def display_results(self, df):
        self.tree.clear()
        for _, row in df.iterrows():
            item = QTreeWidgetItem([str(row['Source']), str(row['Destination'])])
            self.tree.addTopLevelItem(item)
    
    def save_output(self, df, source_path):
        output_dir = os.path.dirname(source_path)
        output_file = os.path.join(output_dir, f"processed_{os.path.basename(source_path)}")
        df.to_excel(output_file, index=False)
        self.status_label.setText(f"Saved processed file: {output_file}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CablePlanProcessor()
    window.show()
    sys.exit(app.exec_())