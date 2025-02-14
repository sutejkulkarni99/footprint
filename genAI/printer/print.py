import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import win32print
import win32ui
import os

# Function to check if the printer is connected
def is_printer_connected(printer_name):
    try:
        # Attempt to get the printer status
        printer_info = win32print.GetPrinter(win32print.OpenPrinter(printer_name), 2)
        return True
    except Exception as e:
        return False

# Function to send the .pto file to the printer
def print_pto_file(file_path):
    try:
        # Get the default printer
        printer_name = win32print.GetDefaultPrinter()

        # Check if the printer is connected
        if not is_printer_connected(printer_name):
            messagebox.showerror("Printer Error", f"Printer '{printer_name}' is not connected.")
            return

        # Open the .pto file as a binary file
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Create a DC (Device Context) for the printer
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Brother P-Touch Print")
        hdc.StartPage()

        # Send raw data to the printer (this assumes the printer can handle raw .pto data)
        hdc.WritePrinter(file_data)

        # Finish the print job
        hdc.EndPage()
        hdc.EndDoc()

        messagebox.showinfo("Success", f"Printed file: {file_path}")

    except Exception as e:
        messagebox.showerror("Print Error", f"An error occurred while printing {file_path}: {str(e)}")

# Function to browse and select a folder, then list .pto files
def browse_folder():
    folder_path = filedialog.askdirectory(title="Select Folder Containing P-touch Files")
    
    if folder_path:
        # List only .pto files in the folder
        pto_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pto')]
        
        if pto_files:
            # Clear any previous list in the GUI
            file_listbox.delete(0, tk.END)
            
            # Insert files into the listbox
            for file in pto_files:
                file_listbox.insert(tk.END, file)
            
            # Store the folder path in the entry widget for future printing
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder_path)
        else:
            messagebox.showwarning("No Files", "No .pto files found in the selected folder.")

# Function to filter the listbox based on search input
def search_files():
    search_query = search_entry.get().lower()
    # Loop through all items and hide those that don't match the search query
    for index in range(file_listbox.size()):
        file_name = file_listbox.get(index).lower()
        if search_query in file_name:
            file_listbox.itemconfig(index, {'bg':'white'})  # Show the file
        else:
            file_listbox.itemconfig(index, {'bg':'gray'})  # Hide the file

# Function to update preview image when a file is selected
def update_preview(event):
    selected_file = file_listbox.get(file_listbox.curselection())
    if selected_file:
        preview_image_path = os.path.join(folder_entry.get(), selected_file.replace('.pto', '.png'))  # Assuming you have a corresponding PNG file for preview
        if os.path.exists(preview_image_path):
            try:
                # Open the image file using Pillow
                image = Image.open(preview_image_path)
                image = image.resize((300, 200))  # Resize to fit the preview area
                photo = ImageTk.PhotoImage(image)

                # Update the label with the image
                preview_label.config(image=photo)
                preview_label.image = photo  # Keep a reference to avoid garbage collection
            except Exception as e:
                messagebox.showerror("Error", f"Could not load preview image: {str(e)}")
        else:
            preview_label.config(image='')  # Clear preview if no image is found
    else:
        preview_label.config(image='')  # Clear preview if no file is selected

# Function to print selected .pto files (supporting multiple selection)
def print_selected_files():
    # Get the selected files from the listbox
    selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
    
    if not selected_files:
        messagebox.showwarning("No Selection", "Please select at least one file to print.")
        return
    
    folder_path = folder_entry.get()
    for file in selected_files:
        file_path = os.path.join(folder_path, file)
        print_pto_file(file_path)

# Set up the Tkinter GUI
root = tk.Tk()
root.title("P-Touch Label Printer")

# Set up the frame for layout
frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Left Frame for list and scrollbar
left_frame = tk.Frame(frame)
left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# Scrollbar and listbox for files
scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
file_listbox = tk.Listbox(left_frame, selectmode=tk.MULTIPLE, width=50, height=20, yscrollcommand=scrollbar.set)
scrollbar.config(command=file_listbox.yview)

# Add scrollbar to the listbox
file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Right Frame for folder selection, search bar, and print button
right_frame = tk.Frame(frame)
right_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# Folder path entry and browse button
folder_label = tk.Label(right_frame, text="Select Folder Containing .PTO Files:")
folder_label.pack(pady=10)

folder_entry = tk.Entry(right_frame, width=40)
folder_entry.pack(pady=5)

browse_button = tk.Button(right_frame, text="Browse Folder", command=browse_folder)
browse_button.pack(pady=10)

# Search bar at the top-right
search_label = tk.Label(right_frame, text="Search Files:")
search_label.pack(pady=10)

search_entry = tk.Entry(right_frame, width=40)
search_entry.pack(pady=5)
search_entry.bind('<KeyRelease>', lambda event: search_files())  # Update search as the user types

# Preview Label
preview_label = tk.Label(right_frame, text="Preview will be shown here")
preview_label.pack(pady=10)

# Button to print selected .pto files
print_button = tk.Button(right_frame, text="Print Selected Files", command=print_selected_files)
print_button.pack(pady=20)

# Bind the update preview function to the selection event
file_listbox.bind('<<ListboxSelect>>', update_preview)

# Run the GUI
root.mainloop()
