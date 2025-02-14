import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# Function to process and extract relevant data from the CSV file
def extract_connections(df):
    connections = []

    # Clean up the dataframe (skip first few rows with metadata)
    df_clean = df.iloc[6:].reset_index(drop=True)
    
    # Reorganize columns for clarity
    df_clean.columns = ['Index', 'Empty', 'Signal', 'd [mm²]', 'Feature', 'Color', 'Empty2', 'Pin', 'Pin Contact', 'Pin2', 'Pin2 Contact']
    
    # Filter necessary columns
    df_clean = df_clean[['Pin', 'Signal', 'Pin Contact', 'Pin2 Contact']]

    # Iterate through the rows and extract the connection information
    for _, row in df_clean.iterrows():
        ix_pin = str(row['Pin'])  # Pin from IX connector
        ix_signal = str(row['Signal'])  # Signal from IX connector
        ix_pin_contact = str(row['Pin Contact'])  # Crimp type for IX pin
        matnet_pin_contact = str(row['Pin2 Contact'])  # Crimp type for Matnet pin

        # Check for Pin 1 and Pin 2 of IX connector (Channel 2)
        if ix_pin == '1' or ix_pin == '2':
            matnet_pin = 'Pin ' + ix_pin  # Matnet pin 1 or 2
            connection_data = {
                'IX Pin': ix_pin,
                'IX Signal': ix_signal,
                'IX Pin Contact': ix_pin_contact,
                'Matnet Pin': matnet_pin,
                'Matnet Pin Contact': matnet_pin_contact
            }
            connections.append(connection_data)
        
        # Check for Pin 6 and Pin 7 of IX connector (Channel 1)
        elif ix_pin == '6' or ix_pin == '7':
            matnet_pin = 'Pin ' + str(int(ix_pin) - 4)  # Pin 6 maps to Matnet Pin 2, Pin 7 maps to Matnet Pin 2
            connection_data = {
                'IX Pin': ix_pin,
                'IX Signal': ix_signal,
                'IX Pin Contact': ix_pin_contact,
                'Matnet Pin': matnet_pin,
                'Matnet Pin Contact': matnet_pin_contact
            }
            connections.append(connection_data)

    return connections

# Function to save extracted connections to a CSV file
def save_connections_to_csv(connections, output_file):
    connections_df = pd.DataFrame(connections)
    connections_df.to_csv(output_file, index=False)
    messagebox.showinfo("Success", f"Connections saved to {output_file}")

# Function to open file dialog and load CSV
def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    
    try:
        df = pd.read_csv(file_path)
        
        # Get extracted connections from the dataframe
        connections = extract_connections(df)
        
        # Generate output CSV file path
        output_file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if output_file:
            save_connections_to_csv(connections, output_file)
        
    except Exception as e:
        messagebox.showerror("Error", f"Error reading the file: {str(e)}")

# Set up the GUI
root = tk.Tk()
root.title("Data Extractor")

# Frame for displaying the table
frame_table = tk.Frame(root)
frame_table.pack(padx=10, pady=10)

# Buttons for opening files and exporting
btn_open = tk.Button(root, text="Open CSV File", command=open_file)
btn_open.pack(pady=5)

# Start the GUI main loop
root.mainloop()
