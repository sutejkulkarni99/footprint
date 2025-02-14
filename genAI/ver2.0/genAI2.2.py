import pandas as pd
import os
from tkinter import Tk, filedialog, Button, Label
from transformers import LayoutLMv3ForSequenceClassification, LayoutLMv3Tokenizer

# Initialize the AI model and tokenizer
tokenizer = LayoutLMv3Tokenizer.from_pretrained("microsoft/layoutlmv3-base")
model = LayoutLMv3ForSequenceClassification.from_pretrained("microsoft/layoutlmv3-base")

def ai_extract_relevant_data(input_file):
    """
    Use AI model to extract relevant data from an unstructured Excel file.
    """
    try:
        df = pd.read_excel(input_file, header=None)
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return []

    # Flatten the table into text for AI processing
    table_text = "\n".join(["\t".join(map(str, row)) for row in df.values if not all(pd.isnull(row))])

    # Tokenize and pass the table to the model
    inputs = tokenizer(table_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model(**inputs)

    # Mock AI processing: Extract relevant rows based on custom logic
    relevant_rows = df.iloc[5:, :]  # Example: Skip header rows and extract all rows starting from the 5th row

    # Extract connector data based on column structure
    extracted_data = []
    for _, row in relevant_rows.iterrows():
        if pd.notnull(row[0]):  # Assuming column 0 contains "Pin" information
            extracted_data.append({
                "From_Pin": row[0],
                "To_Pin": row[5],
                "Length": 1000,  # Replace with actual logic to extract length
                "Feature": row[3] if pd.notnull(row[3]) else "None",
                "From_Contact": row[6] if pd.notnull(row[6]) else "Unknown",
                "To_Contact": row[8] if pd.notnull(row[8]) else "Unknown",
            })

    return extracted_data

def create_output_file(extracted_data, output_file):
    """
    Create a new Excel file with the extracted data in the desired format.
    """
    if not extracted_data:
        print("No data extracted. Aborting file creation.")
        return

    output_df = pd.DataFrame(extracted_data)
    output_df.columns = ["From_Pin", "To_Pin", "Length (mm)", "Feature", "From_Contact", "To_Contact"]
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_df.to_excel(output_file, index=False)
    print(f"Output file saved to {output_file}")

def process_files(input_file, output_file):
    """
    Process the input file and generate the output file.
    """
    print("Extracting data from input file...")
    extracted_data = ai_extract_relevant_data(input_file)
    if not extracted_data:
        print("No relevant data found to extract.")
        return

    print("Data extracted successfully.")
    print("Creating output file...")
    create_output_file(extracted_data, output_file)
    print("Output file created successfully.")

def select_input_file():
    """
    Opens a file dialog to select the input Excel file.
    """
    input_file = filedialog.askopenfilename(title="Select Input Excel File", filetypes=[("Excel Files", "*.xlsx;*.xls")])
    if input_file:
        input_file_label.config(text=f"Input File: {input_file}")
        return input_file
    return None

def select_output_file():
    """
    Opens a file dialog to select the output location and file name.
    """
    output_file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx;*.xls")], title="Select Output File Location")
    if output_file:
        output_file_label.config(text=f"Output File: {output_file}")
        return output_file
    return None

def run_extraction():
    """
    Trigger the extraction process based on selected input and output file paths.
    """
    input_file = select_input_file()
    if not input_file:
        return
    
    output_file = select_output_file()
    if not output_file:
        return
    
    process_files(input_file, output_file)

# Set up the main GUI window
root = Tk()
root.title("AI Data Extraction from Excel")
root.geometry("400x200")

# UI elements
input_file_label = Label(root, text="Input File: Not Selected", wraplength=350)
input_file_label.pack(pady=10)

output_file_label = Label(root, text="Output File: Not Selected", wraplength=350)
output_file_label.pack(pady=10)

process_button = Button(root, text="Select Files and Process", command=run_extraction)
process_button.pack(pady=20)

# Run the GUI
root.mainloop()
