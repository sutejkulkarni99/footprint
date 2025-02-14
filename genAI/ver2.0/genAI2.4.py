import pandas as pd
from transformers import LayoutLMv3ForSequenceClassification, LayoutLMv3Tokenizer
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os


# Initialize the AI model and tokenizer
tokenizer = LayoutLMv3Tokenizer.from_pretrained("microsoft/layoutlmv3-base")
model = LayoutLMv3ForSequenceClassification.from_pretrained("microsoft/layoutlmv3-base")


def ai_extract_relevant_data(input_file):
    """
    Use AI model to extract relevant data from an unstructured Excel file.
    """
    try:
        # Normalize file path to absolute path
        input_file = os.path.abspath(input_file)
        print(f"Processing file: {input_file}")  # Log the file path

        # Load the Excel file
        df = pd.read_excel(input_file, header=None)
        print(f"Excel file loaded. Shape of the data: {df.shape}")

        # Flatten the table into text for AI processing
        table_text = "\n".join(["\t".join(map(str, row)) for row in df.values if not all(pd.isnull(row))])
        print(f"Table text generated. Length of table text: {len(table_text)}")

        # Tokenize and pass the table to the model
        inputs = tokenizer(table_text, return_tensors="pt", max_length=512, truncation=True)
        print(f"Input tokens generated. Token length: {len(inputs['input_ids'][0])}")

        # Model inference
        outputs = model(**inputs)
        print(f"Model inference completed.")

        # Mock AI processing: Extract relevant rows based on custom logic
        relevant_rows = df.iloc[5:, :]  # Example: Skip header rows and extract all rows starting from the 5th row
        print(f"Relevant rows extracted: {relevant_rows.shape}")

        # Extract connector data based on column structure
        extracted_data = []
        for _, row in relevant_rows.iterrows():
            if pd.notnull(row[0]):  # Assuming column 0 contains "Pin" information
                extracted_data.append({
                    "From_Pin": row[0],
                    "To_Pin": row[5] if pd.notnull(row[5]) else "Unknown",
                    "Length": 1000,  # Mock length data
                    "Feature": row[3] if pd.notnull(row[3]) else "None",
                    "From_Contact": row[6] if pd.notnull(row[6]) else "Unknown",
                    "To_Contact": row[8] if pd.notnull(row[8]) else "Unknown",
                })

        print(f"Data extraction complete. Total records extracted: {len(extracted_data)}")
        return extracted_data

    except Exception as e:
        raise ValueError(f"Error processing the input file: {e}")


def create_output_file(extracted_data, output_file, output_format):
    try:
        # Normalize file path to absolute path
        output_file = os.path.abspath(output_file)
        print(f"Saving output to: {output_file}")

        # Convert the extracted data to a DataFrame
        output_df = pd.DataFrame(extracted_data)

        # Ensure the directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save to the selected format
        if output_format == 'excel':
            output_df.to_excel(output_file, index=False)
        elif output_format == 'csv':
            output_df.to_csv(output_file, index=False)
        elif output_format == 'xml':
            output_df.to_xml(output_file, index=False)

        print(f"Output file saved to {output_file}")

    except Exception as e:
        raise ValueError(f"Error saving the output file: {e}")


# GUI function to select the input Excel file
def select_input_file():
    input_file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
    return input_file


# GUI function to select the output file path and format
def select_output_file(output_format):
    filetypes = {
        'excel': [("Excel Files", "*.xlsx")],
        'csv': [("CSV Files", "*.csv")],
        'xml': [("XML Files", "*.xml")]
    }

    output_file = filedialog.asksaveasfilename(defaultextension=f".{output_format}", filetypes=filetypes[output_format])
    return output_file


# Function to run the extraction and file creation process
def run_extraction(input_file, output_file, output_format, progress_label):
    try:
        # Log the input file path being used
        print(f"Input file selected: {input_file}")
        print(f"Output file selected: {output_file}")

        # Update progress label
        progress_label.config(text="Extracting data from input file... Please wait.")
        extracted_data = ai_extract_relevant_data(input_file)

        # Update progress label
        progress_label.config(text="Creating output file... Please wait.")
        create_output_file(extracted_data, output_file, output_format)

        messagebox.showinfo("Success", "Data extraction and output file creation completed successfully!")
        progress_label.config(text="Processing complete!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        progress_label.config(text="Error occurred during processing!")


# Function to create the GUI layout
def create_gui():
    window = tk.Tk()
    window.title("AI Data Extraction Tool")

    # Title label
    label = tk.Label(window, text="Welcome to the AI Data Extraction Tool", font=("Arial", 14))
    label.pack(pady=10)

    # Input file selection
    input_button = tk.Button(window, text="Select Input Excel File", command=lambda: input_file_entry.config(state='normal'))
    input_button.pack(pady=10)

    input_file_entry = tk.Entry(window, width=50)
    input_file_entry.pack(pady=5)
    input_file_entry.config(state='disabled')

    # Output file selection
    output_button = tk.Button(window, text="Select Output File", command=lambda: output_file_entry.config(state='normal'))
    output_button.pack(pady=10)

    output_file_entry = tk.Entry(window, width=50)
    output_file_entry.pack(pady=5)
    output_file_entry.config(state='disabled')

    # File format selection
    format_label = tk.Label(window, text="Select Output Format:", font=("Arial", 10))
    format_label.pack(pady=5)

    format_options = ['excel', 'csv', 'xml']
    format_combobox = ttk.Combobox(window, values=format_options, state='readonly', width=20)
    format_combobox.set('excel')  # Default to Excel
    format_combobox.pack(pady=5)

    # Progress label
    progress_label = tk.Label(window, text="No processing done yet.", font=("Arial", 10))
    progress_label.pack(pady=10)

    # Start processing button
    start_button = tk.Button(window, text="Start Processing",
                             command=lambda: run_extraction(input_file_entry.get(), output_file_entry.get(),
                                                            format_combobox.get(), progress_label))
    start_button.pack(pady=20)

    # Open file dialogs for input and output files
    def open_input_dialog():
        input_file_path = select_input_file()
        input_file_entry.delete(0, tk.END)
        input_file_entry.insert(0, input_file_path)

    def open_output_dialog():
        output_format = format_combobox.get()
        output_file_path = select_output_file(output_format)
        output_file_entry.delete(0, tk.END)
        output_file_entry.insert(0, output_file_path)

    input_button.config(command=open_input_dialog)
    output_button.config(command=open_output_dialog)

    # Start the GUI
    window.mainloop()


if __name__ == "__main__":
    create_gui()
