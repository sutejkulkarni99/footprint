import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QInputDialog,
    QProgressBar, QMessageBox, QTextEdit, QScrollArea
)
from PySide6.QtGui import QImage, QPixmap, QTextCursor
from PySide6.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph import GridItem
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


class PinCalibrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pin Detection and Calibration")
        self.setGeometry(100, 100, 1200, 800)

        # Variables
        self.image_path = None
        self.image_rgb = None
        self.rotated_image = None  # Stores the rotated image
        self.num_pins = 0
        self.pin_rows = []  # Stores multiple rows of pins
        self.current_row = []  # Stores pins for the current row
        self.calibration_points = []  # Stores ruler calibration points
        self.pixel_to_mm_ratio = None  # Pixel-to-mm conversion factor
        self.line_points = []  # Stores two points for the red line
        self.rotation_angle = None  # Angle for image rotation
        self.dragging = False  # Flag to track if the user is drawing a line
        self.selecting_pins = False  # Flag to track if the user is selecting pins
        self.selecting_corners = False  # Flag to track if the user is selecting corners
        self.document_corners = []  # Stores the four corners of the document

        # Standard pitch sizes (in mm)
        self.standard_pitch_sizes = [
            0.3, 0.5, 0.8, 1.0, 1.27, 1.5, 2.0, 2.5, 2.54, 3.5, 3.81, 3.96, 4.2, 5.0, 5.08, 6.3
        ]

        # Colors for different rows of pins
        self.row_colors = ['r', 'g', 'b', 'c', 'm', 'y']

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Left panel for controls
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)
        self.layout.addWidget(self.control_panel, stretch=1)

        # Right panel for image display
        self.image_panel = QWidget()
        self.image_layout = QVBoxLayout(self.image_panel)
        self.layout.addWidget(self.image_panel, stretch=3)

        # Apply the color scheme
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;  /* Dark blue-gray background */
                color: #ECEFF4;  /* Light gray text */
                font-size: 14px;
            }
            QPushButton {
                background-color: #4C566A;  /* Medium blue-gray */
                color: #ECEFF4;  /* Light gray text */
                border-radius: 10px;  /* Rounded edges */
                padding: 10px;
                font-size: 16px;
                border: 2px solid #4C566A;  /* Border color */
            }
            QPushButton:hover {
                background-color: #5E81AC;  /* Lighter blue on hover */
                border: 2px solid #5E81AC;
            }
            QPushButton:pressed {
                background-color: #81A1C1;  /* Even lighter blue when pressed */
            }
            QPushButton:focus {
                border: 2px solid #D08770;  /* Warm orange accent for focus */
            }
            QLabel {
                color: #ECEFF4;  /* Light gray text */
                font-size: 14px;
            }
            QProgressBar {
                background-color: #4C566A;  /* Medium blue-gray */
                color: #ECEFF4;  /* Light gray text */
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;  /* Light blue for progress */
                border-radius: 5px;
            }
            QTextEdit {
                background-color: #3B4252;  /* Darker background for the text area */
                color: #ECEFF4;  /* Light gray text */
                font-size: 14px;
                border: 1px solid #4C566A;  /* Border color */
                border-radius: 5px;  /* Rounded edges */
                padding: 10px;
            }
        """)

        # Add buttons and labels to the control panel
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        self.control_layout.addWidget(self.load_button)

        self.select_corners_button = QPushButton("Select Document Corners")
        self.select_corners_button.clicked.connect(self.start_selecting_corners)
        self.select_corners_button.setEnabled(False)
        self.control_layout.addWidget(self.select_corners_button)

        self.calibrate_button = QPushButton("Calibrate Ruler")
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.calibrate_button.setEnabled(False)
        self.control_layout.addWidget(self.calibrate_button)

        self.submit_calibration_button = QPushButton("Submit Calibration Points")
        self.submit_calibration_button.clicked.connect(self.submit_calibration_points)
        self.submit_calibration_button.setEnabled(False)
        self.control_layout.addWidget(self.submit_calibration_button)

        self.select_pins_button = QPushButton("Select Pins")
        self.select_pins_button.clicked.connect(self.start_selecting_pins)
        self.select_pins_button.setEnabled(False)
        self.control_layout.addWidget(self.select_pins_button)

        self.submit_row_button = QPushButton("Submit Row")
        self.submit_row_button.clicked.connect(self.submit_row)
        self.submit_row_button.setEnabled(False)
        self.control_layout.addWidget(self.submit_row_button)

        self.add_row_button = QPushButton("Add New Row")
        self.add_row_button.clicked.connect(self.add_new_row)
        self.add_row_button.setEnabled(False)
        self.control_layout.addWidget(self.add_row_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setEnabled(False)
        self.control_layout.addWidget(self.reset_button)

        self.calculate_pitch_button = QPushButton("Calculate Pitch")
        self.calculate_pitch_button.clicked.connect(self.calculate_pitch)
        self.calculate_pitch_button.setEnabled(False)
        self.control_layout.addWidget(self.calculate_pitch_button)

        self.generate_drawing_button = QPushButton("Generate 2D Drawing")
        self.generate_drawing_button.clicked.connect(self.generate_2d_drawing)
        self.generate_drawing_button.setEnabled(False)
        self.control_layout.addWidget(self.generate_drawing_button)

        # Replace QLabel with QTextEdit for results
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)  # Make it read-only
        self.control_layout.addWidget(self.result_text_edit)

        # PyQtGraph image display
        self.image_view = pg.ImageView()
        self.image_layout.addWidget(self.image_view)

        # Scatter plot items for pins and calibration points
        self.pin_scatter = pg.ScatterPlotItem(pen='r', symbol='o', size=10, brush='r')
        self.calibration_scatter = pg.ScatterPlotItem(pen='b', symbol='x', size=10, brush='b')
        self.image_view.getView().addItem(self.pin_scatter)
        self.image_view.getView().addItem(self.calibration_scatter)

        # Line plot item for the red line
        self.red_line = pg.PlotCurveItem(pen='r')
        self.image_view.getView().addItem(self.red_line)

        # Add a grid to the image view
        self.grid = GridItem()
        self.image_view.getView().addItem(self.grid)
        self.grid.hide()  # Hide the grid initially

        # Connect mouse events
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)

    def update_result_text(self, text):
        """
        Update the result text in the QTextEdit widget.
        """
        self.result_text_edit.setPlainText(text)  # Use setPlainText for plain text
        self.result_text_edit.moveCursor(QTextCursor.End)  # Scroll to the bottom

    def load_image(self):
        # Open file dialog to select an image
        self.image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if not self.image_path:
            return

        # Load the image
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            QMessageBox.critical(self, "Error", "Could not load image.")
            return

        # Convert to RGB for display
        self.image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)

        # Display the image in PyQtGraph
        self.display_image(self.image_rgb)

        # Enable corner selection
        self.select_corners_button.setEnabled(True)
        self.update_result_text("Image loaded. Click 'Select Document Corners' to start.")

    def display_image(self, image):
        # Display the image in PyQtGraph
        self.image_view.setImage(np.rot90(image, k=-1))  # Rotate to correct orientation
        self.image_view.getView().invertY(False)  # Ensure y-axis is not inverted

    def start_selecting_corners(self):
        # Clear previous corner points
        self.document_corners = []
        self.selecting_corners = True
        self.update_result_text("Click on the four corners of the document.")

    def on_mouse_click(self, event):
        if self.selecting_corners:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Add the point to the document corners
            self.document_corners.append((x, y))
            self.calibration_scatter.addPoints([x], [y])  # Add visual marker

            if len(self.document_corners) == 4:
                # Disable further corner selection
                self.selecting_corners = False
                self.update_result_text("Four corners selected. Applying perspective correction...")

                # Apply perspective correction
                self.apply_perspective_correction()

    def apply_perspective_correction(self):
        if len(self.document_corners) != 4:
            QMessageBox.critical(self, "Error", "Please select four corners first.")
            return

        # Get the dimensions of the original image
        height, width = self.image_rgb.shape[:2]

        # Define the target points for the perspective transform
        # Use the selected corners as the source points
        src_points = np.array(self.document_corners, dtype="float32")

        # Define the target points to maintain the selected region's proportions
        # Calculate the bounding box of the selected region
        min_x = min(point[0] for point in self.document_corners)
        max_x = max(point[0] for point in self.document_corners)
        min_y = min(point[1] for point in self.document_corners)
        max_y = max(point[1] for point in self.document_corners)

        # Define the target points to cover the entire image
        target_points = np.array([
            [min_x, min_y],
            [max_x, min_y],
            [max_x, max_y],
            [min_x, max_y]
        ], dtype="float32")

        # Calculate the perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_points, target_points)
        print(matrix)
        # Apply the perspective transform to the entire image
        self.rotated_image = cv2.warpPerspective(self.image_rgb, matrix, (width, height))

        # Display the transformed image
        self.display_image(self.rotated_image)

        # Enable calibration
        self.calibrate_button.setEnabled(True)
        self.update_result_text("Document straightened. Click 'Calibrate Ruler' to proceed.")

    def start_calibration(self):
        # Clear previous calibration points
        self.calibration_points = []
        self.calibration_scatter.clear()

        # Enable calibration point selection
        self.update_result_text("Click on the image to select two calibration points on the ruler.")
        self.image_view.scene.sigMouseClicked.connect(self.on_calibration_click)

        # Show and update the grid
        self.toggle_grid(True)
        self.update_grid_spacing()

    def on_calibration_click(self, event):
        if len(self.calibration_points) < 2:
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())
            self.calibration_points.append((x, y))
            self.calibration_scatter.addPoints([x], [y])  # Add visual marker
            self.update_result_text(f"Calibration point {len(self.calibration_points)} placed at ({x}, {y}).")

            if len(self.calibration_points) == 2:
                # Disable further calibration point selection
                self.image_view.scene.sigMouseClicked.disconnect(self.on_calibration_click)
                self.update_result_text("Two calibration points placed. Click 'Submit Calibration Points' to proceed.")
                self.submit_calibration_button.setEnabled(True)

    def submit_calibration_points(self):
        if len(self.calibration_points) != 2:
            QMessageBox.critical(self, "Error", "Please select exactly two calibration points.")
            return

        # Create a QInputDialog for entering the known distance
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Calibration")
        dialog.setLabelText("Enter the known distance between the two points (in mm):")
        dialog.setInputMode(QInputDialog.DoubleInput)
        dialog.setDoubleMinimum(0.1)  # Set the minimum value to 0.1
        dialog.setDoubleValue(10.0)  # Set the default value to 10.0

        # Show the dialog and get the result
        ok = dialog.exec()
        if ok:
            known_distance_mm = dialog.doubleValue()
            if known_distance_mm <= 0:
                QMessageBox.critical(self, "Error", "Invalid distance. Please enter a positive number.")
                return

            # Calculate the pixel-to-millimeter ratio
            (x1, y1), (x2, y2) = self.calibration_points
            distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self.pixel_to_mm_ratio = distance_pixels / known_distance_mm

            self.update_result_text(f"Calibration complete. Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.4f} mm/pixel")

            # Hide the grid
            self.toggle_grid(False)

            # Enable pin selection
            self.select_pins_button.setEnabled(True)
            self.update_result_text("Calibration complete. Click 'Select Pins' to start placing pins.")

    def start_selecting_pins(self):
        # Enable pin selection
        self.selecting_pins = True
        self.current_row = []
        self.update_result_text("Click on the image to select pins for the current row.")
        self.image_view.scene.sigMouseClicked.connect(self.on_pin_click)

        # Enable submit and add row buttons
        self.submit_row_button.setEnabled(True)
        self.add_row_button.setEnabled(True)

    def on_pin_click(self, event):
        if self.selecting_pins:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Add the pin to the current row
            self.current_row.append((x, y))

            # Add visual marker for the pin
            color = self.row_colors[len(self.pin_rows) % len(self.row_colors)]
            self.pin_scatter.addPoints([x], [y], pen=color, brush=color)

            self.update_result_text(f"Pin {len(self.current_row)} placed at ({x}, {y}).")

    def submit_row(self):
        if len(self.current_row) > 0:
            # Add the current row to the list of rows
            self.pin_rows.append(self.current_row)
            self.current_row = []

            # Disable pin selection for the current row
            self.image_view.scene.sigMouseClicked.disconnect(self.on_pin_click)
            self.selecting_pins = False

            # Enable pitch calculation and reset calibration
            self.calculate_pitch_button.setEnabled(True)
            self.reset_button.setEnabled(True)

            self.update_result_text("Row submitted. Click 'Add New Row' to add another row or 'Calculate Pitch' to proceed.")

    def add_new_row(self):
        if len(self.current_row) > 0:
            # Submit the current row before starting a new one
            self.submit_row()

        # Start selecting pins for a new row
        self.start_selecting_pins()

    def calculate_pitch(self):
        if len(self.pin_rows) < 1:
            QMessageBox.critical(self, "Error", "At least one row of pins is required to calculate pitch.")
            return

        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Calibration not done. Please calibrate first.")
            return

        # Calculate pitch distances for each row
        result_text = "Pin pitch distances (in mm):\n"
        for row_idx, row in enumerate(self.pin_rows):
            pitch_distances = []
            for i in range(len(row) - 1):
                x1, y1 = row[i]
                x2, y2 = row[i + 1]
                distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                distance_mm = distance_pixels / self.pixel_to_mm_ratio
                pitch_distances.append(distance_mm)

            # Display the results for the current row
            result_text += f"Row {row_idx + 1}:\n"
            for i, distance in enumerate(pitch_distances):
                nearest_pitch = self.approximate_pitch(distance)
                result_text += f"  Pin {i+1} to Pin {i+2}: {distance:.2f} mm (Nearest standard: {nearest_pitch} mm)\n"

        # Calculate separation between rows
        if len(self.pin_rows) > 1:
            result_text += "\nRow separation (in mm):\n"
            for i in range(len(self.pin_rows) - 1):
                y1 = self.pin_rows[i][0][1]  # Y position of the first pin in the current row
                y2 = self.pin_rows[i + 1][0][1]  # Y position of the first pin in the next row
                separation_pixels = abs(y2 - y1)
                separation_mm = separation_pixels / self.pixel_to_mm_ratio
                result_text += f"  Row {i+1} to Row {i+2}: {separation_mm:.2f} mm\n"

        self.update_result_text(result_text)

        # Enable the "Generate 2D Drawing" button
        self.generate_drawing_button.setEnabled(True)

    def approximate_pitch(self, pitch_value):
        """
        Approximate the given pitch value to the nearest standard pitch size.
        """
        # Find the nearest standard pitch size
        nearest_pitch = min(self.standard_pitch_sizes, key=lambda x: abs(x - pitch_value))
        return nearest_pitch

    def generate_2d_drawing(self):
        if len(self.pin_rows) < 1:
            QMessageBox.critical(self, "Error", "At least one row of pins is required to generate a 2D drawing.")
            return

        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Calibration not done. Please calibrate first.")
            return

        # Create the 2D drawing
        fig, ax = plt.subplots()
        ax.set_aspect('equal')

        # Plot the holes for each row
        hole_diameter = 1.0  # 1.0mm diameter
        hole_radius = hole_diameter / 2

        for row_idx, row in enumerate(self.pin_rows):
            color = self.row_colors[row_idx % len(self.row_colors)]
            x_positions = [pin[0] for pin in row]
            y_position = row[0][1]  # Use the first pin's y position for the row

            for x in x_positions:
                circle = Circle((x, y_position), hole_radius, edgecolor=color, facecolor='none')
                ax.add_patch(circle)

            # Add hole diameter information
            for x in x_positions:
                ax.text(x, y_position + 2 * hole_radius, f'⌀{hole_diameter}mm', 
                        fontsize=8, ha='center', va='bottom', color=color)

            # Add pitch markings
            for i in range(len(x_positions) - 1):
                x1 = x_positions[i]
                x2 = x_positions[i + 1]
                pitch = self.approximate_pitch((x2 - x1) / self.pixel_to_mm_ratio)
                mid_x = (x1 + x2) / 2

                # Draw a dashed line for the pitch
                ax.plot([x1, x2], [y_position - 1.5 * hole_radius, y_position - 1.5 * hole_radius], 
                        color=color, linestyle='--')

                # Add pitch text below the dashed line
                ax.text(mid_x, y_position - 2.5 * hole_radius, f'PITCH {pitch:.2f}mm', 
                        fontsize=8, ha='center', va='top', color=color)

        # Set plot limits with extra padding to avoid text overlap
        all_x = [pin[0] for row in self.pin_rows for pin in row]
        all_y = [pin[1] for row in self.pin_rows for pin in row]
        ax.set_xlim(min(all_x) - 5, max(all_x) + 5)
        ax.set_ylim(min(all_y) - 5, max(all_y) + 5)

        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add labels
        ax.set_xlabel("X Position (mm)")
        ax.set_ylabel("Y Position (mm)")
        ax.set_title("2D Drawing of Pin Holes")

        # Save the plot as a JPG or PNG file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save 2D Drawing", "", "Image Files (*.jpg *.png)")
        if file_path:
            plt.savefig(file_path, dpi=300, bbox_inches='tight')  # Save with high resolution
            plt.close()  # Close the figure to free memory
            self.update_result_text(f"2D drawing saved to {file_path}")
        else:
            plt.close()  # Close the figure if the user cancels
            self.update_result_text("2D drawing not saved.")

    def reset(self):
        # Reset all variables and UI elements
        self.image_path = None
        self.image_rgb = None
        self.rotated_image = None
        self.num_pins = 0
        self.pin_rows = []
        self.current_row = []
        self.calibration_points = []
        self.line_points = []
        self.rotation_angle = None
        self.dragging = False
        self.selecting_pins = False
        self.selecting_corners = False
        self.document_corners = []

        self.pin_scatter.clear()
        self.calibration_scatter.clear()
        self.red_line.clear()
        self.image_view.clear()

        self.load_button.setEnabled(True)
        self.select_corners_button.setEnabled(False)
        self.calibrate_button.setEnabled(False)
        self.submit_calibration_button.setEnabled(False)
        self.select_pins_button.setEnabled(False)
        self.submit_row_button.setEnabled(False)
        self.add_row_button.setEnabled(False)
        self.calculate_pitch_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.generate_drawing_button.setEnabled(False)

        self.update_result_text("Results will be displayed here.")

    def toggle_grid(self, visible):
        """Toggle the visibility of the grid."""
        self.grid.setVisible(visible)

    def update_grid_spacing(self):
        """Update the grid spacing based on the calibration ratio."""
        if self.pixel_to_mm_ratio is not None:
            spacing_mm = 1.0  # 1mm grid spacing
            spacing_pixels = spacing_mm * self.pixel_to_mm_ratio
            self.grid.setSpacing(spacing_pixels)


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec())