import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import re
from collections import defaultdict

class ConnectorTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Visual Connector Trainer")
        self.root.geometry("1200x800")
        
        # Data storage
        self.df = None
        self.selections = []
        self.current_selection = None
        self.pattern_db = defaultdict(list)
        self.cell_size = 100
        
        # GUI Components
        self.create_widgets()
        self.bind_events()
    
    def create_widgets(self):
        # File Selection
        ttk.Button(self.root, text="Load Excel File", command=self.load_file).pack(pady=5)
        
        # Create canvas with scrollbars
        self._create_scrollable_canvas()
        
        # Selection controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5)
        
        self.connector_var = tk.StringVar()
        ttk.Label(control_frame, text="Connector Name:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(control_frame, textvariable=self.connector_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Confirm Selection", command=self.save_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Train Model", command=self.train_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        ttk.Label(self.root, textvariable=self.status_var).pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_scrollable_canvas(self):
        self.canvas = tk.Canvas(self.root, bg='white')
        
        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Inner frame
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # Event bindings
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
    
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.finalize_selection)
    
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.df = pd.read_excel(file_path)
            self.draw_sheet()
            self.status_var.set(f"Loaded: {file_path}")
    
    def draw_sheet(self):
        # Clear existing items
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        cols = self.df.columns.tolist()
        
        # Draw column headers
        for col_idx, col_name in enumerate(cols):
            header = ttk.Label(self.inner_frame, text=col_name, width=15, 
                              borderwidth=1, relief="solid", background='#e0e0e0')
            header.grid(row=0, column=col_idx, sticky='nsew')
        
        # Draw cells
        for row_idx in range(len(self.df)):
            for col_idx in range(len(cols)):
                value = str(self.df.iat[row_idx, col_idx])
                cell = ttk.Label(self.inner_frame, text=value, width=15, 
                                borderwidth=1, relief="solid", wraplength=150)
                cell.grid(row=row_idx+1, column=col_idx, sticky='nsew')
        
        # Update canvas scroll region
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def start_selection(self, event):
        col = event.x // self.cell_size
        row = (event.y - 30) // 30
        if row >= 0 and col >= 0:
            self.current_selection = {
                'start_col': col,
                'start_row': row,
                'end_col': col,
                'end_row': row,
                'rect': None
            }
    
    def update_selection(self, event):
        if self.current_selection:
            col = event.x // self.cell_size
            row = max((event.y - 30) // 30, 0)
            
            self.current_selection['end_col'] = col
            self.current_selection['end_row'] = row
            
            if self.current_selection['rect']:
                self.canvas.delete(self.current_selection['rect'])
            
            x1 = min(self.current_selection['start_col'], col) * self.cell_size
            y1 = 30 + min(self.current_selection['start_row'], row) * 30
            x2 = (max(self.current_selection['start_col'], col) + 1) * self.cell_size
            y2 = 30 + (max(self.current_selection['start_row'], row) + 1) * 30
            
            # Corrected line with proper parenthesis
            self.current_selection['rect'] = self.canvas.create_rectangle(
                x1, y1, x2, y2, outline='blue', width=2, dash=(4,4))
    def finalize_selection(self, event):
        if self.current_selection:
            self.status_var.set("Selection finalized. Enter connector name and confirm")
    
    def save_selection(self):
        if not self.current_selection or not self.connector_var.get():
            messagebox.showwarning("Input Error", "Make a selection and enter connector name!")
            return
        
        # Get selected data
        cols = self.df.columns.tolist()
        min_col = min(self.current_selection['start_col'], self.current_selection['end_col'])
        max_col = max(self.current_selection['start_col'], self.current_selection['end_col'])
        min_row = min(self.current_selection['start_row'], self.current_selection['end_row'])
        max_row = max(self.current_selection['start_row'], self.current_selection['end_row'])
        
        pins = []
        for row_idx in range(min_row, max_row+1):
            for col_idx in range(min_col, max_col+1):
                pins.append(str(self.df.iat[row_idx, col_idx]))
        
        self.selections.append({
            'connector': self.connector_var.get(),
            'pins': pins,
            'location': (min_col, min_row, max_col, max_row)
        })
        
        self.connector_var.set("")
        self.current_selection = None
        self.canvas.delete("selection")
        self.status_var.set(f"Saved {len(pins)} pins for connector {self.selections[-1]['connector']}")
    
    def train_model(self):
        if not self.selections:
            messagebox.showwarning("No Data", "Make selections first!")
            return
        
        # Extract patterns from selections
        pattern_counts = defaultdict(int)
        for selection in self.selections:
            for text in selection['pins']:
                # Find connector-pin patterns
                matches = re.findall(r'([A-Za-z]+)\s*[\-\_/]?\s*(\d+)', text)
                for match in matches:
                    pattern = f"{match[0]}-{match[1]}"
                    pattern_counts[pattern] += 1
        
        # Create pattern database with confidence scores
        total = sum(pattern_counts.values())
        for pattern, count in pattern_counts.items():
            confidence = count / total
            self.pattern_db[pattern] = confidence
        
        messagebox.showinfo("Training Complete", 
                          f"Learned {len(self.pattern_db)} patterns with average confidence {sum(self.pattern_db.values())/len(self.pattern_db):.2f}")
    
    def reset(self):
        self.selections = []
        self.pattern_db = defaultdict(list)
        self.canvas.delete("all")
        self.status_var.set("Reset complete")
        self.draw_sheet()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConnectorTrainer(root)
    root.mainloop()