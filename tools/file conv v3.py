import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QTreeWidget, QTreeWidgetItem, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QPointF
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
        
        # Graphics View for Diagram
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        layout.addWidget(self.graphics_view)
        
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
            df_patterns = pd.read_excel(training_data_path, sheet_name='Patterns')
            df_connections = pd.read_excel(training_data_path, sheet_name='Connections')
            for _, row in df_patterns.iterrows():
                source = row['Source']
                target = row['Target']
                self.connector_patterns[source].append(target)
            self.connections = df_connections.values.tolist()
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
            self.draw_diagram(output)
    
    def process_batch(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Open Excel Files", "", "Excel Files (*.xlsx)")
        for file in files:
            output = self.process_file(file)
            self.save_output(output, file)
            self.draw_diagram(output)
    
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
    
    def draw_diagram(self, df):
        self.graphics_scene.clear()
        pin_positions = {}
        x_offset = 50
        y_offset = 50
        x_spacing = 150
        y_spacing = 50
        
        # Draw pins and connections
        for idx, row in df.iterrows():
            source = str(row['Source'])
            destination = str(row['Destination'])
            
            if source not in pin_positions:
                pin_positions[source] = (x_offset, y_offset + len(pin_positions) * y_spacing)
                self.draw_pin(source, pin_positions[source])
            
            if destination not in pin_positions:
                pin_positions[destination] = (x_offset + x_spacing, y_offset + len(pin_positions) * y_spacing)
                self.draw_pin(destination, pin_positions[destination])
            
            self.draw_connection(pin_positions[source], pin_positions[destination])
    
    def draw_pin(self, pin_name, position):
        x, y = position
        ellipse = QGraphicsEllipseItem(x, y, 20, 20)
        text = QGraphicsTextItem(pin_name)
        text.setPos(x + 25, y)
        self.graphics_scene.addItem(ellipse)
        self.graphics_scene.addItem(text)
    
    def draw_connection(self, start_pos, end_pos):
        x1, y1 = start_pos
        x2, y2 = end_pos
        line = QGraphicsLineItem(x1 + 10, y1 + 10, x2 + 10, y2 + 10)
        self.graphics_scene.addItem(line)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CablePlanProcessor()
    window.show()
    sys.exit(app.exec_())