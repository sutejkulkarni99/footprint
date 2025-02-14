import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

def process_excel():
    try:
        # Open a file dialog to select an Excel file
        input_file = filedialog.askopenfilename(
            title="Select an Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if not input_file:
            messagebox.showwarning("No File Selected", "Please select a file to proceed.")
            return

        # Read the Excel file without headers
        df = pd.read_excel(input_file, header=None)

        # Check if "PIN" exists in the first column (case-insensitive)
        pin_row_index = df[df.iloc[:, 0].str.contains("PIN", case=False, na=False)].index

        if pin_row_index.empty:
            messagebox.showerror("Error", "No 'PIN' cell found in the first column.")
            return

        # Get the first occurrence of "PIN"
        pin_row_index = pin_row_index[0]

        # Extract all rows below the first "PIN"
        data_below_pin = df.iloc[pin_row_index + 1:, 0]

        # Remove empty cells and trim whitespace
        data_below_pin = data_below_pin.dropna().str.strip()

        # Filter the data: keep only numeric values below 100
        valid_pin_numbers = data_below_pin[
            data_below_pin.apply(lambda x: x.isdigit() and int(x) < 100)
        ]

        # Debug: Print extracted and valid PINs
        print("Data below PIN:")
        print(data_below_pin)
        print("Valid PIN Numbers:")
        print(valid_pin_numbers)

        # Check if there are valid PIN numbers
        if valid_pin_numbers.empty:
            messagebox.showinfo("No Valid PINs", "No valid PIN numbers (numeric values below 100) were found.")
            return

        # Create a new DataFrame with the filtered data
        new_df = pd.DataFrame(valid_pin_numbers, columns=["PIN Numbers"])

        # Save the new DataFrame to an Excel file
        output_file = filedialog.asksaveasfilename(
            title="Save Processed File As",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )

        if output_file:
            new_df.to_excel(output_file, index=False)
            messagebox.showinfo("Success", f"Valid PIN numbers have been saved to {output_file}")
        else:
            messagebox.showwarning("Save Canceled", "File save was canceled.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create the main GUI window
root = tk.Tk()
root.title("Excel PIN Processor")

# Set up the GUI layout
label = tk.Label(root, text="Upload an Excel file to extract valid PIN numbers", font=("Arial", 12))
label.pack(pady=10)

process_button = tk.Button(root, text="Upload and Process Excel File", command=process_excel, font=("Arial", 12), bg="lightblue")
process_button.pack(pady=20)

# Run the GUI event loop
root.mainloop()
