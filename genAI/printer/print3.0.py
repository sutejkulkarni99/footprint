import sys
import os
import subprocess
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QScrollArea, \
                            QFileDialog, QListWidget, QListWidgetItem

class LBXFileExplorer(QWidget):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("LBX File Explorer")
        self.setGeometry(300, 100, 600, 400)

        self.folder_path = ""
        self.selected_file = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Chat-like search bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search .lbx files...")  # Placeholder text
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border-radius: 20px;
                padding: 10px;
                font-size: 16px;
                border: 1px solid #ccc;
            }
            QLineEdit:focus {
                border: 1px solid #0061F2;  /* Border turns blue on focus */
                background-color: #ffffff;
            }
        """)
        self.search_input.textChanged.connect(self.filter_files)

        # Browse Folder button with light grey color
        self.browse_button = QPushButton("Browse Folder", self)
        self.browse_button.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                padding: 10px;
                background-color: #f5f5f5;  /* Light grey background */
                color: #333333;  /* Dark grey text */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;  /* Slightly darker grey on hover */
            }
        """)
        self.browse_button.clicked.connect(self.browse_folder)

        # Open File button with the same style as the browse button
        self.open_button = QPushButton("Open", self)
        self.open_button.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                padding: 10px;
                background-color: #f5f5f5;  /* Light grey background */
                color: #333333;  /* Dark grey text */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;  /* Slightly darker grey on hover */
            }
        """)
        self.open_button.setEnabled(False)  # Initially disabled
        self.open_button.clicked.connect(self.open_file)

        # File list display area
        self.file_area = QScrollArea(self)
        self.file_area.setWidgetResizable(True)
        
        # Create a QWidget to hold the QListWidget (this is necessary to place it inside a QScrollArea)
        self.file_widget = QWidget()
        self.file_list = QListWidget(self.file_widget)  # Use QListWidget for the file list
        
        self.file_area.setWidget(self.file_widget)

        # Add widgets to the layout
        layout.addWidget(self.search_input)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.file_area)
        layout.addWidget(self.open_button)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path = folder
            self.display_files()

    def display_files(self):
        # Clear current list
        self.file_list.clear()

        # Display .lbx files
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".lbx"):
                list_item = QListWidgetItem(filename)
                list_item.setData(Qt.UserRole, filename)  # Store filename in item data
                self.file_list.addItem(list_item)

        # Connect item selection
        self.file_list.itemClicked.connect(self.select_file)

    def select_file(self, item):
        self.selected_file = item.data(Qt.UserRole)
        self.open_button.setEnabled(True)  # Enable the Open button when a file is selected

    def open_file(self):
        if self.selected_file:
            file_path = os.path.join(self.folder_path, self.selected_file)
            # Open the file using subprocess.Popen to prevent hanging
            subprocess.Popen(["start", "ptouch.exe", file_path], shell=True)

    def filter_files(self):
        search_text = self.search_input.text().lower()

        # Clear current list
        self.file_list.clear()

        # Display filtered files
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".lbx") and search_text in filename.lower():
                list_item = QListWidgetItem(filename)
                list_item.setData(Qt.UserRole, filename)  # Store filename in item data
                self.file_list.addItem(list_item)

        # Connect item selection
        self.file_list.itemClicked.connect(self.select_file)

# Main part to run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = LBXFileExplorer()
    ex.show()
    sys.exit(app.exec_())
