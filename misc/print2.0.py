import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess


class FileExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("P-Touch Label File Explorer")
        self.root.geometry("600x400")

        self.current_path = ""  # To hold the current directory path
        self.files = []  # List of files in the current folder

        self.init_ui()

    def init_ui(self):
        # Top Bar: Browse Button
        self.top_frame = tk.Frame(self.root, bd=2, relief="groove")
        self.top_frame.pack(side="top", fill="x")

        self.browse_button = tk.Button(self.top_frame, text="Browse Folder", command=self.browse_folder)
        self.browse_button.pack(side="left", padx=10, pady=5)

        self.path_label = tk.Label(self.top_frame, text="No folder selected", anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True, padx=10)

        # Right Pane: Search and File List
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(fill="both", expand=True)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_file_list)

        self.search_entry = tk.Entry(self.right_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="top", padx=10, pady=5)

        self.scrollbar = tk.Scrollbar(self.right_frame, orient="vertical")
        self.file_list = tk.Listbox(self.right_frame, yscrollcommand=self.scrollbar.set, height=15)
        self.scrollbar.config(command=self.file_list.yview)

        self.file_list.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        # Double-click on a file to open
        self.file_list.bind("<Double-1>", self.open_file)

    def browse_folder(self):
        """Open a folder selection dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.current_path = folder
            self.path_label.config(text=self.current_path)
            self.load_files()

    def load_files(self):
        """Load .lbx files from the selected folder."""
        try:
            self.files = [
                f for f in os.listdir(self.current_path)
                if os.path.isfile(os.path.join(self.current_path, f)) and f.lower().endswith(".lbx")
            ]
            self.update_file_list()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading files: {e}")

    def update_file_list(self, *args):
        """Filter and update the file list based on the search query."""
        search_term = self.search_var.get().lower()
        self.file_list.delete(0, tk.END)
        for file in self.files:
            if search_term in file.lower():
                self.file_list.insert(tk.END, file)

    def open_file(self, event):
        """Open the selected file using the default application."""
        selected_file = self.file_list.get(tk.ACTIVE)
        if selected_file:
            file_path = os.path.join(self.current_path, selected_file)
            try:
                subprocess.Popen([file_path], shell=True)
            except Exception as e:
                messagebox.showerror("Error", f"Error opening file: {e}")
        else:
            messagebox.showwarning("No File Selected", "Please select a file to open.")


# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = FileExplorerApp(root)
    root.mainloop()
