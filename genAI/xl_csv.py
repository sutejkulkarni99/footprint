import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os

class XLSXtoTSVConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("XLSX to TSV Converter")
        
        # Input File Selection
        self.input_frame = tk.Frame(self.root, padx=10, pady=10)
        self.input_frame.pack(fill=tk.X)
        
        self.input_label = tk.Label(self.input_frame, text="Select XLSX File:")
        self.input_label.pack(side=tk.LEFT)
        
        self.input_entry = tk.Entry(self.input_frame, width=40)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        
        self.input_button = tk.Button(self.input_frame, text="Browse", command=self.browse_input)
        self.input_button.pack(side=tk.LEFT)
        
        # Output Directory Selection
        self.output_frame = tk.Frame(self.root, padx=10, pady=10)
        self.output_frame.pack(fill=tk.X)
        
        self.output_label = tk.Label(self.output_frame, text="Output Directory:")
        self.output_label.pack(side=tk.LEFT)
        
        self.output_entry = tk.Entry(self.output_frame, width=40)
        self.output_entry.pack(side=tk.LEFT, padx=5)
        
        self.output_button = tk.Button(self.output_frame, text="Browse", command=self.browse_output)
        self.output_button.pack(side=tk.LEFT)
        
        # Convert Button
        self.convert_button = tk.Button(self.root, text="Convert to TSV", command=self.convert)
        self.convert_button.pack(pady=10)
        
        # Status Label
        self.status_label = tk.Label(self.root, text="", fg="gray")
        self.status_label.pack(pady=5)
    
    def browse_input(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx")],
            title="Select Excel File"
        )
        if file_path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, file_path)
    
    def browse_output(self):
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dir_path)
    
    def convert(self):
        input_path = self.input_entry.get()
        output_dir = self.output_entry.get()
        
        if not input_path or not output_dir:
            messagebox.showerror("Error", "Please select both input file and output directory")
            return
        
        try:
            # Read Excel file
            df = pd.read_excel(input_path, engine='openpyxl')
            
            # Create output filename
            base_name = os.path.basename(input_path).replace(".xlsx", ".tsv")
            output_path = os.path.join(output_dir, base_name)
            
            # Save as TSV
            df.to_csv(output_path, sep='\t', index=False)
            
            self.status_label.config(text=f"Conversion successful!\nSaved to: {output_path}", fg="green")
            messagebox.showinfo("Success", "File converted successfully!")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", f"Conversion failed:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = XLSXtoTSVConverter(root)
    root.mainloop()