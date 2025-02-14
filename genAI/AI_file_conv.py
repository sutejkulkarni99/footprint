import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import os
from transformers import pipeline
import re

class CablePlanProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Cable Plan Processor")
        self.root.geometry("1200x800")
        
        # Initialize AI Model for pattern recognition
        self.nlp = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
        
        # Configure GUI
        self.create_widgets()
        self.source_file = None
        self.connector_patterns = {}
        
    def create_widgets(self):
        # File Selection
        ttk.Button(self.root, text="Load Source File", command=self.load_file).grid(row=0, column=0, padx=5, pady=5)
        
        # Processing Controls
        ttk.Button(self.root, text="Process Single File", command=self.process_single).grid(row=0, column=1, padx=5)
        ttk.Button(self.root, text="Process Batch", command=self.process_batch).grid(row=0, column=2, padx=5)
        
        # Results Display
        self.tree = ttk.Treeview(self.root, columns=("Source", "Destination"), show="headings")
        self.tree.heading("Source", text="Source Connector/Pin")
        self.tree.heading("Destination", text="Destination Connector/Pin")
        self.tree.grid(row=1, column=0, columnspan=3, sticky='nsew')
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.root, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=1, column=3, sticky='ns')
        hsb.grid(row=2, column=0, columnspan=3, sticky='ew')
        
        # Status Bar
        self.status = ttk.Label(self.root, text="Ready")
        self.status.grid(row=3, column=0, columnspan=3, sticky='w')
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def load_file(self):
        self.source_file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if self.source_file:
            self.status.config(text=f"Loaded: {os.path.basename(self.source_file)}")
            self.analyze_patterns(self.source_file)
            
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
        pattern_db = {}
        for conn in connections:
            parts = re.split(r'\s+', conn)
            if len(parts) >= 4:
                source = f"{parts[0]} {parts[1]}"
                target = f"{parts[2]} {parts[3]}"
                pattern_db.setdefault(source, []).append(target)
        
        self.connector_patterns = pattern_db
        self.status.config(text=f"Learned {len(pattern_db)} connection patterns")
    
    def process_single(self):
        if self.source_file:
            output = self.process_file(self.source_file)
            self.display_results(output)
            self.save_output(output, self.source_file)
    
    def process_batch(self):
        files = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xlsx")])
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
        self.tree.delete(*self.tree.get_children())
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row['Source'], row['Destination']))
    
    def save_output(self, df, source_path):
        output_dir = os.path.dirname(source_path)
        output_file = os.path.join(output_dir, f"processed_{os.path.basename(source_path)}")
        df.to_excel(output_file, index=False)
        self.status.config(text=f"Saved processed file: {output_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CablePlanProcessor(root)
    root.mainloop()