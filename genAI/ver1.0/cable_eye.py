import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM

# Initialize DistilGPT2
model_name = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def process_excel(input_file, output_file):
    # Read the Excel file
    df = pd.read_excel(input_file, skiprows=4)  # Adjust to match your layout

    # Extract and clean relevant columns
    df_cleaned = df[['Pin', 'Signal', 'd [mm²]', 'Feature', 'Color', 'Pin.1', 'Contact']].dropna(how='all')

    # Process data
    output_data = []
    length = "1000 mm"  # Set the fixed length from the Excel file
    for i, row in df_cleaned.iterrows():
        # Prepare text input for DistilGPT2 (optional)
        input_text = f"Pin {row['Pin']} ({row['Signal']}, {row['Color']}) connects to Pin {row['Pin.1']} ({row['Contact']})"
        tokens = tokenizer.encode(input_text, return_tensors="pt")
        output_tokens = model.generate(tokens, max_length=50)
        generated_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)

        # Append processed data
        output_data.append({
            "From Pin": row['Pin'],
            "From Signal": row['Signal'],
            "To Pin": row['Pin.1'],
            "To Signal": generated_text,  # Use the model's output if needed
            "Length": length,
            "Diameter [mm²]": row['d [mm²]'],
            "Feature": row['Feature'],
            "Color": row['Color'],
        })

    # Convert output data to DataFrame
    output_df = pd.DataFrame(output_data)

    # Save to Excel
    output_df.to_excel(output_file, index=False)

# GUI Application
def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, file_path)

def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, file_path)

def process_file():
    input_file = input_entry.get()
    output_file = output_entry.get()
    if not input_file or not output_file:
        messagebox.showerror("Error", "Please select both input and output files.")
        return
    try:
        process_excel(input_file, output_file)
        messagebox.showinfo("Success", f"File processed and saved to {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create GUI
root = tk.Tk()
root.title("CableEye Data Processor")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Input file
input_label = tk.Label(frame, text="Input Excel File:")
input_label.grid(row=0, column=0, sticky="e")
input_entry = tk.Entry(frame, width=50)
input_entry.grid(row=0, column=1, padx=5)
input_button = tk.Button(frame, text="Browse", command=browse_file)
input_button.grid(row=0, column=2, padx=5)

# Output file
output_label = tk.Label(frame, text="Output Excel File:")
output_label.grid(row=1, column=0, sticky="e")
output_entry = tk.Entry(frame, width=50)
output_entry.grid(row=1, column=1, padx=5)
output_button = tk.Button(frame, text="Save As", command=save_file)
output_button.grid(row=1, column=2, padx=5)

# Process button
process_button = tk.Button(root, text="Process File", command=process_file, bg="green", fg="white")
process_button.pack(pady=10)

# Run the GUI
root.mainloop()
