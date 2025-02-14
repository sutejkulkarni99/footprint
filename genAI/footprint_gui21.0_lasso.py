import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QInputDialog,
    QProgressBar, QMessageBox, QTextEdit, QScrollArea, QGridLayout
)
from PySide6.QtGui import QImage, QPixmap, QTextCursor
from PySide6.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph import GridItem
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
import cadquery as cq
from cadquery import exporters


class PinCalibrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pin Detection and Calibration")
        self.setGeometry(100, 100, 1200, 800)

        # Variables
        self.image_path = None
        self.image_rgb = None
        self.num_pins = 0
        self.pin_rows = []  # Stores multiple rows of pins
        self.current_row = []  # Stores pins for the current row
        self.square_points = []  # Stores the four corners of the square
        self.calibration_points = []  # Stores ruler calibration points
        self.pixel_to_mm_ratio = None  # Pixel-to-mm ratio from ruler calibration
        self.homography_matrix = None  # Homography matrix for angular correction
        self.selecting_square = False  # Flag to track if the user is selecting a square
        self.selecting_calibration = False  # Flag to track if the user is calibrating
        self.selecting_pins = False  # Flag to track if the user is selecting pins
        self.selecting_mounting_hole = False  # Flag to track if the user is selecting mounting holes
        self.selecting_border = False  # Flag to track if the user is selecting a border
        self.selecting_lasso = False  # Flag to track if the user is selecting a lasso

        # New variables for lasso selection
        self.lasso_points = []  # Stores points for the lasso selection
        self.lasso_line = None  # Stores the line item for the lasso
        self.lasso_scatter = None  # Stores the scatter plot item for the lasso points

        # Initialize border_size and mounting_holes
        self.border_size = 5.0  # Default border size in mm
        self.mounting_holes = []  # Stores mounting hole positions

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
        self.control_layout = QGridLayout(self.control_panel)  # Use QGridLayout
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
                padding: 5px;  /* Smaller padding */
                font-size: 12px;  /* Smaller font size */
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

        # Add buttons and labels to the control panel in two columns
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        self.load_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.load_button, 0, 0)  # Row 0, Column 0

        self.square_button = QPushButton("Select Square")
        self.square_button.clicked.connect(self.start_selecting_square)
        self.square_button.setEnabled(False)
        self.square_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.square_button, 1, 0)  # Row 1, Column 0

        self.calibrate_button = QPushButton("Calibrate Ruler")
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.calibrate_button.setEnabled(False)
        self.calibrate_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.calibrate_button, 2, 0)  # Row 2, Column 0

        self.pins_button = QPushButton("Select Pins")
        self.pins_button.clicked.connect(self.start_selecting_pins)
        self.pins_button.setEnabled(False)
        self.pins_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.pins_button, 3, 0)  # Row 3, Column 0

        self.add_row_button = QPushButton("Add New Row")
        self.add_row_button.clicked.connect(self.add_new_row)
        self.add_row_button.setEnabled(False)
        self.add_row_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.add_row_button, 4, 0)  # Row 4, Column 0

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setEnabled(False)
        self.reset_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.reset_button, 5, 0)  # Row 5, Column 0

        self.calculate_pitch_button = QPushButton("Calculate Pitch")
        self.calculate_pitch_button.clicked.connect(self.calculate_pitch)
        self.calculate_pitch_button.setEnabled(False)
        self.calculate_pitch_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.calculate_pitch_button, 6, 0)  # Row 6, Column 0

        # Add "Lasso Select" button before file generation buttons
        self.add_lasso_button = QPushButton("Lasso Select")
        self.add_lasso_button.clicked.connect(self.start_lasso_selection)
        self.add_lasso_button.setEnabled(False)  # Initially disabled
        self.add_lasso_button.setFixedSize(150, 40)
        self.control_layout.addWidget(self.add_lasso_button, 7, 0)  # Row 7, Column 0

        # File generation buttons
        self.generate_drawing_button = QPushButton("Generate 2D Drawing")
        self.generate_drawing_button.clicked.connect(self.generate_2d_drawing)
        self.generate_drawing_button.setEnabled(False)
        self.generate_drawing_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.generate_drawing_button, 8, 0)  # Row 8, Column 0

        self.generate_step_button = QPushButton("Generate STEP File")
        self.generate_step_button.clicked.connect(self.generate_step_file_dialog)
        self.generate_step_button.setEnabled(False)
        self.generate_step_button.setFixedSize(150, 40)  # Larger button size
        self.control_layout.addWidget(self.generate_step_button, 9, 0)  # Row 9, Column 0

        # Replace QLabel with QTextEdit for results
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)  # Make it read-only
        self.control_layout.addWidget(self.result_text_edit, 10, 0, 1, 2)  # Row 10, Span 2 columns

        # PyQtGraph image display
        self.image_view = pg.ImageView()
        self.image_layout.addWidget(self.image_view)

        # Scatter plot items for pins, calibration points, and square corners
        self.pin_scatter = pg.ScatterPlotItem(pen='r', symbol='o', size=10, brush='r')
        self.calibration_scatter = pg.ScatterPlotItem(pen='b', symbol='x', size=10, brush='b')
        self.square_scatter = pg.ScatterPlotItem(pen='g', symbol='s', size=10, brush='g')
        self.image_view.getView().addItem(self.pin_scatter)
        self.image_view.getView().addItem(self.calibration_scatter)
        self.image_view.getView().addItem(self.square_scatter)

        # Connect mouse events
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)
        self.image_view.scene.sigMouseMoved.connect(self.on_mouse_move)

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

        # Enable square selection
        self.square_button.setEnabled(True)
        self.update_result_text("Image loaded. Click 'Select Square' to start.")

    def display_image(self, image):
        # Display the image in PyQtGraph
        self.image_view.setImage(np.rot90(image, k=-1))  # Rotate to correct orientation
        self.image_view.getView().invertY(False)  # Ensure y-axis is not inverted

    def start_selecting_square(self):
        # Clear previous square points
        self.square_points = []
        self.square_scatter.clear()

        # Enable square point selection
        self.selecting_square = True
        self.selecting_calibration = False  # Disable other modes
        self.selecting_pins = False  # Disable other modes
        self.selecting_mounting_hole = False  # Disable other modes
        self.selecting_border = False  # Disable other modes
        self.selecting_lasso = False  # Disable other modes

        # Change button text
        self.square_button.setText("Submit Square Points")
        self.square_button.clicked.disconnect()
        self.square_button.clicked.connect(self.submit_square_points)

        # Disconnect any previous connections to avoid multiple triggers
        try:
            self.image_view.scene.sigMouseClicked.disconnect()
        except TypeError:
            pass  # Ignore if no connections exist

        # Connect the mouse click event
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)

        self.update_result_text("Click on the image to select the four corners of the square.")

    def on_mouse_click(self, event):
        if self.selecting_square:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Add the point to the square points
            self.square_points.append((x, y))
            self.square_scatter.addPoints([x], [y])  # Add visual marker
            self.update_result_text(f"Square corner {len(self.square_points)} placed at ({x}, {y}).")

            if len(self.square_points) == 4:
                # Disable further square point selection
                self.selecting_square = False
                self.image_view.scene.sigMouseClicked.disconnect(self.on_mouse_click)
                self.update_result_text("Four corners of the square selected. Click 'Submit Square Points' to proceed.")
                self.calibrate_button.setEnabled(True)

        elif self.selecting_calibration:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Add the point to the calibration points
            self.calibration_points.append((x, y))
            self.calibration_scatter.addPoints([x], [y])  # Add visual marker
            self.update_result_text(f"Calibration point {len(self.calibration_points)} placed at ({x}, {y}).")

            if len(self.calibration_points) == 2:
                # Disable further calibration point selection
                self.selecting_calibration = False
                self.image_view.scene.sigMouseClicked.disconnect(self.on_mouse_click)
                self.update_result_text("Two calibration points placed. Click 'Submit Calibration Points' to proceed.")
                self.pins_button.setEnabled(True)

        elif self.selecting_pins:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Add the pin to the current row
            self.current_row.append((x, y))

            # Add visual marker for the pin
            color = self.row_colors[len(self.pin_rows) % len(self.row_colors)]
            self.pin_scatter.addPoints([x], [y], pen=color, brush=color)

            self.update_result_text(f"Pin {len(self.current_row)} placed at ({x}, {y}).")

            # Change button text after placing the first pin
            if len(self.current_row) == 1:
                self.pins_button.setText("Submit Row")
                self.pins_button.clicked.disconnect()
                self.pins_button.clicked.connect(self.submit_row)

        elif self.selecting_lasso:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Check if the new point is very close to the first point
            if len(self.lasso_points) > 0:
                first_x, first_y = self.lasso_points[0]
                distance = np.sqrt((x - first_x)**2 + (y - first_y)**2)
                if distance < 10:  # Threshold for considering the point as the same
                    x, y = first_x, first_y  # Snap to the first point

            # Add the point to the lasso points
            self.lasso_points.append((x, y))

            # Update the scatter plot with all points
            self.lasso_scatter.setData([p[0] for p in self.lasso_points], [p[1] for p in self.lasso_points])

            # Draw lines between the points to visualize the perimeter
            if len(self.lasso_points) > 1:
                x1, y1 = self.lasso_points[-2]
                x2, y2 = self.lasso_points[-1]
                if self.lasso_line:
                    self.image_view.getView().removeItem(self.lasso_line)
                self.lasso_line = pg.PlotCurveItem([x1, x2], [y1, y2], pen='y')
                self.image_view.getView().addItem(self.lasso_line)

            self.update_result_text(f"Perimeter point {len(self.lasso_points)} placed at ({x}, {y}).")

            # If the new point is the same as the first point, complete the polygon
            if len(self.lasso_points) > 2 and (x, y) == self.lasso_points[0]:
                self.submit_lasso()

    def on_mouse_move(self, pos):
        if self.selecting_lasso and len(self.lasso_points) > 0:
            # Get the position relative to the view and map it to the scene
            scene_pos = self.image_view.getView().mapSceneToView(pos)
            x, y = int(scene_pos.x()), int(scene_pos.y())

            # Draw a temporary line from the last point to the current mouse position
            x1, y1 = self.lasso_points[-1]
            if self.lasso_line:
                self.image_view.getView().removeItem(self.lasso_line)
            self.lasso_line = pg.PlotCurveItem([x1, x], [y1, y], pen='y')
            self.image_view.getView().addItem(self.lasso_line)

    def submit_square_points(self):
        if len(self.square_points) != 4:
            QMessageBox.critical(self, "Error", "Please select four corners of the square first.")
            return

        # Define the source points (selected square corners)
        src_points = np.array(self.square_points, dtype="float32")

        # Define the destination points (e.g., a perfect square)
        side_length = max(
            np.linalg.norm(src_points[0] - src_points[1]),
            np.linalg.norm(src_points[1] - src_points[2]),
            np.linalg.norm(src_points[2] - src_points[3]),
            np.linalg.norm(src_points[3] - src_points[0])
        )
        dst_points = np.array([
            [0, 0],
            [side_length, 0],
            [side_length, side_length],
            [0, side_length]
        ], dtype="float32")

        # Calculate the homography matrix
        self.homography_matrix, _ = cv2.findHomography(src_points, dst_points)

        # Calculate angular deviation (skew in degrees)
        angle = self.calculate_angular_deviation(src_points)
        self.update_result_text(f"Square points submitted. Angular deviation: {angle:.2f} degrees.")

        # Enable ruler calibration
        self.calibrate_button.setEnabled(True)

    def calculate_angular_deviation(self, src_points):
        """
        Calculate the angular deviation (skew in degrees) of the square.
        """
        # Calculate vectors for two adjacent sides of the square
        vector1 = src_points[1] - src_points[0]
        vector2 = src_points[3] - src_points[0]

        # Calculate the angle between the vectors
        angle = np.degrees(np.arccos(np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))))

        return angle

    def start_calibration(self):
        # Clear previous calibration points
        self.calibration_points = []
        self.calibration_scatter.clear()

        # Enable calibration point selection
        self.selecting_calibration = True
        self.selecting_square = False  # Disable other modes
        self.selecting_pins = False  # Disable other modes
        self.selecting_mounting_hole = False  # Disable other modes
        self.selecting_border = False  # Disable other modes
        self.selecting_lasso = False  # Disable other modes

        # Change button text
        self.calibrate_button.setText("Submit Calibration Points")
        self.calibrate_button.clicked.disconnect()
        self.calibrate_button.clicked.connect(self.submit_calibration_points)

        # Disconnect any previous connections to avoid multiple triggers
        try:
            self.image_view.scene.sigMouseClicked.disconnect()
        except TypeError:
            pass  # Ignore if no connections exist

        # Connect the mouse click event
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)

        self.update_result_text("Click on the image to select two calibration points on the ruler.")

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

            # Transform the calibration points using the homography matrix
            (x1, y1), (x2, y2) = self.calibration_points
            src_points = np.array([[x1, y1], [x2, y2]], dtype="float32").reshape(-1, 1, 2)
            dst_points = cv2.perspectiveTransform(src_points, self.homography_matrix)

            # Calculate the Euclidean distance between the transformed points
            (x1_corrected, y1_corrected), (x2_corrected, y2_corrected) = dst_points.reshape(-1, 2)
            distance_pixels = np.sqrt((x2_corrected - x1_corrected)**2 + (y2_corrected - y1_corrected)**2)

            # Calculate the pixel-to-millimeter ratio
            self.pixel_to_mm_ratio = distance_pixels / known_distance_mm

            print(f"Debug: pixel_to_mm_ratio = {self.pixel_to_mm_ratio}")  # Debugging statement

            self.update_result_text(f"Calibration complete. Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.4f} mm/pixel")

            # Enable pin selection and STEP file generation
            self.pins_button.setEnabled(True)
            self.generate_step_button.setEnabled(True)  # Enable STEP file generation
            self.update_result_text("Calibration complete. Click 'Select Pins' to start placing pins.")

    def start_selecting_pins(self):
        # Enable pin selection
        self.selecting_pins = True
        self.selecting_square = False  # Disable other modes
        self.selecting_calibration = False  # Disable other modes
        self.selecting_mounting_hole = False  # Disable other modes
        self.selecting_border = False  # Disable other modes
        self.selecting_lasso = False  # Disable other modes

        # Clear the current row
        self.current_row = []

        # Change button text
        self.pins_button.setText("Submit Row")
        self.pins_button.clicked.disconnect()
        self.pins_button.clicked.connect(self.submit_row)

        # Disconnect any previous connections to avoid multiple triggers
        try:
            self.image_view.scene.sigMouseClicked.disconnect()
        except TypeError:
            pass  # Ignore if no connections exist

        # Connect the mouse click event
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)

        self.update_result_text("Click on the image to select pins for the current row.")

        # Enable submit and add row buttons
        self.add_row_button.setEnabled(True)

    def submit_row(self):
        if len(self.current_row) > 0:
            # Add the current row to the list of rows
            self.pin_rows.append(self.current_row)
            self.current_row = []

            # Disable pin selection for the current row
            self.image_view.scene.sigMouseClicked.disconnect(self.on_mouse_click)
            self.selecting_pins = False

            # Enable pitch calculation, reset calibration, and STEP file generation
            self.calculate_pitch_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.generate_step_button.setEnabled(True)  # Enable STEP file generation

            # Enable "Lasso Select" button
            self.add_lasso_button.setEnabled(True)

            self.update_result_text("Row submitted. Click 'Add New Row' to add another row or 'Calculate Pitch' to proceed.")

    def add_new_row(self):
        if len(self.current_row) > 0:
            # Submit the current row before starting a new one
            self.submit_row()

        # Start selecting pins for a new row
        self.start_selecting_pins()

    def calculate_pitch(self):
        print(f"Debug: pixel_to_mm_ratio = {self.pixel_to_mm_ratio}")  # Debugging statement

        if len(self.pin_rows) < 1:
            QMessageBox.critical(self, "Error", "At least one row of pins is required to calculate pitch.")
            return

        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Ruler calibration not completed. Please calibrate the ruler first.")
            return

        # Ensure pixel_to_mm_ratio is valid
        if self.pixel_to_mm_ratio <= 0:
            QMessageBox.critical(self, "Error", "Invalid pixel-to-mm ratio. Please recalibrate the ruler.")
            return

        # Calculate pitch distances for each row
        result_text = "Pin pitch distances (in mm):\n"
        for row_idx, row in enumerate(self.pin_rows):
            pitch_distances = []
            for i in range(len(row) - 1):
                x1, y1 = row[i]
                x2, y2 = row[i + 1]

                # Calculate the Euclidean distance between the two pins
                distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                # Convert pixel distance to millimeters using the calibration ratio
                distance_mm = distance_pixels / self.pixel_to_mm_ratio

                # Approximate the pitch to the nearest standard pitch size
                nearest_pitch = self.approximate_pitch(distance_mm)

                pitch_distances.append((distance_mm, nearest_pitch))

            # Display the results for the current row
            result_text += f"Row {row_idx + 1}:\n"
            for i, (distance, nearest_pitch) in enumerate(pitch_distances):
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
            QMessageBox.critical(self, "Error", "Ruler calibration not completed. Please calibrate the ruler first.")
            return

        # Ensure pixel_to_mm_ratio is valid
        if self.pixel_to_mm_ratio <= 0:
            QMessageBox.critical(self, "Error", "Invalid pixel-to-mm ratio. Please recalibrate the ruler.")
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

        # Add perimeter to the plot
        if len(self.lasso_points) > 2:
            polygon = Polygon(self.lasso_points, edgecolor='y', facecolor='none', linestyle='--')
            ax.add_patch(polygon)

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

        # Save the plot as a vector image (SVG) or high-resolution raster image
        file_path, _ = QFileDialog.getSaveFileName(self, "Save 2D Drawing", "", "Vector Image (*.svg);;Image Files (*.jpg *.png)")
        if file_path:
            if file_path.endswith('.svg'):
                plt.savefig(file_path, format='svg', bbox_inches='tight')  # Save as SVG
            else:
                plt.savefig(file_path, dpi=300, bbox_inches='tight')  # Save as high-res raster image
            plt.close()  # Close the figure to free memory
            self.update_result_text(f"2D drawing saved to {file_path}")
        else:
            plt.close()  # Close the figure if the user cancels
            self.update_result_text("2D drawing not saved.")

    def generate_step_file(self, file_path):
        """
        Generate a STEP file from the pin layout.
        """
        if len(self.pin_rows) < 1:
            QMessageBox.critical(self, "Error", "At least one row of pins is required to generate a STEP file.")
            return

        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Ruler calibration not completed. Please calibrate the ruler first.")
            return

        # Ensure pixel_to_mm_ratio is valid
        if self.pixel_to_mm_ratio <= 0:
            QMessageBox.critical(self, "Error", "Invalid pixel-to-mm ratio. Please recalibrate the ruler.")
            return

        # Create a base plate for the pins
        base_thickness = 2.0  # 2mm thickness for the base plate
        base_width = (max([pin[0] for row in self.pin_rows for pin in row]) -
                      min([pin[0] for row in self.pin_rows for pin in row])) / self.pixel_to_mm_ratio
        base_length = (max([pin[1] for row in self.pin_rows for pin in row]) -
                       min([pin[1] for row in self.pin_rows for pin in row])) / self.pixel_to_mm_ratio

        # Add border to the base plate
        if self.border_size > 0:
            base_width += 2 * self.border_size
            base_length += 2 * self.border_size

        # Create the base plate
        base_plate = cq.Workplane("XY").box(base_width, base_length, base_thickness)

        # Add holes for each pin
        for row_idx, row in enumerate(self.pin_rows):
            for pin in row:
                x = pin[0] / self.pixel_to_mm_ratio
                y = pin[1] / self.pixel_to_mm_ratio
                base_plate = base_plate.faces(">Z").workplane().center(x, y).hole(1.0)  # 1.0mm hole diameter

        # Add mounting holes to the base plate
        for hole in self.mounting_holes:
            x = hole[0] / self.pixel_to_mm_ratio
            y = hole[1] / self.pixel_to_mm_ratio
            base_plate = base_plate.faces(">Z").workplane().center(x, y).hole(3.0)  # 3.0mm hole diameter

        # Add lasso perimeter to the base plate
        if len(self.lasso_points) > 2:
            # Convert lasso points to millimeters
            lasso_points_mm = [(x / self.pixel_to_mm_ratio, y / self.pixel_to_mm_ratio) for x, y in self.lasso_points]
            # Create a polygon from the lasso points
            base_plate = base_plate.faces(">Z").workplane().polyline(lasso_points_mm).close().extrude(base_thickness)

        # Export the model to a STEP file
        exporters.export(base_plate, file_path)

        self.update_result_text(f"STEP file saved to {file_path}")

    def generate_step_file_dialog(self):
        """
        Open a file dialog to save the STEP file.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Save STEP File", "", "STEP Files (*.step *.stp)")
        if file_path:
            self.generate_step_file(file_path)

    def start_lasso_selection(self):
        """
        Start the process of lasso selection.
        """
        # Clear previous lasso points
        self.lasso_points = []
        self.lasso_scatter = pg.ScatterPlotItem(pen='y', symbol='o', size=10, brush='y')  # Scatter plot for lasso points
        self.image_view.getView().addItem(self.lasso_scatter)  # Add scatter plot to the view
        self.selecting_lasso = True
        self.selecting_square = False
        self.selecting_calibration = False
        self.selecting_pins = False
        self.selecting_mounting_hole = False
        self.selecting_border = False

        # Change button text
        self.add_lasso_button.setText("Submit Lasso")
        self.add_lasso_button.clicked.disconnect()
        self.add_lasso_button.clicked.connect(self.submit_lasso)

        # Disconnect any previous connections to avoid multiple triggers
        try:
            self.image_view.scene.sigMouseClicked.disconnect()
        except TypeError:
            pass  # Ignore if no connections exist

        # Connect the mouse click event
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)

        # Connect mouse move event for lasso drawing
        self.image_view.scene.sigMouseMoved.connect(self.on_mouse_move)

        self.update_result_text("Click to add points for the perimeter. Right-click to finish.")

    def submit_lasso(self):
        """
        Submit the lasso selection.
        """
        if len(self.lasso_points) < 3:
            QMessageBox.critical(self, "Error", "At least 3 points are required to create a perimeter.")
            return

        # Close the perimeter by connecting the last point to the first point
        x1, y1 = self.lasso_points[-1]
        x2, y2 = self.lasso_points[0]
        if self.lasso_line:
            self.image_view.getView().removeItem(self.lasso_line)
        self.lasso_line = pg.PlotCurveItem([x1, x2], [y1, y2], pen='y')
        self.image_view.getView().addItem(self.lasso_line)

        # Disable lasso selection
        self.selecting_lasso = False
        self.image_view.scene.sigMouseClicked.disconnect(self.on_mouse_click)
        self.image_view.scene.sigMouseMoved.disconnect(self.on_mouse_move)

        # Change button text back
        self.add_lasso_button.setText("Lasso Select")
        self.add_lasso_button.clicked.disconnect()
        self.add_lasso_button.clicked.connect(self.start_lasso_selection)

        self.update_result_text("Perimeter selection submitted.")

    def reset(self):
        # Reset all variables and UI elements
        self.image_path = None
        self.image_rgb = None
        self.num_pins = 0
        self.pin_rows = []
        self.current_row = []
        self.square_points = []
        self.calibration_points = []
        self.pixel_to_mm_ratio = None
        self.homography_matrix = None
        self.selecting_square = False
        self.selecting_calibration = False
        self.selecting_pins = False
        self.selecting_mounting_hole = False
        self.selecting_border = False
        self.selecting_lasso = False
        self.border_size = 5.0
        self.mounting_holes = []
        self.lasso_points = []

        self.pin_scatter.clear()
        self.calibration_scatter.clear()
        self.square_scatter.clear()
        self.image_view.clear()

        self.load_button.setEnabled(True)
        self.square_button.setEnabled(False)
        self.square_button.setText("Select Square")
        self.square_button.clicked.disconnect()
        self.square_button.clicked.connect(self.start_selecting_square)
        self.calibrate_button.setEnabled(False)
        self.calibrate_button.setText("Calibrate Ruler")
        self.calibrate_button.clicked.disconnect()
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.pins_button.setEnabled(False)
        self.pins_button.setText("Select Pins")
        self.pins_button.clicked.disconnect()
        self.pins_button.clicked.connect(self.start_selecting_pins)
        self.add_row_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.calculate_pitch_button.setEnabled(False)
        self.generate_drawing_button.setEnabled(False)
        self.generate_step_button.setEnabled(False)
        self.add_lasso_button.setEnabled(False)

        self.update_result_text("Results will be displayed here.")


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec())