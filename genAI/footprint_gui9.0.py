import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QInputDialog,
    QProgressBar, QMessageBox
)
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
import pyqtgraph as pg


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
        self.pin_coordinates = []  # Stores pin tip coordinates
        self.calibration_points = []  # Stores ruler calibration points
        self.pixel_to_mm_ratio = None  # Pixel-to-mm conversion factor
        self.line_points = []  # Stores two points for the red line
        self.rotation_angle = None  # Angle for image rotation
        self.dragging = False  # Flag to track if the user is drawing a line

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

        # Add buttons and labels to the control panel
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        self.load_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.load_button)

        self.line_button = QPushButton("Draw Line on Ruler")
        self.line_button.clicked.connect(self.start_line_drawing)
        self.line_button.setEnabled(False)
        self.line_button.setStyleSheet("QPushButton { background-color: #FF5722; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.line_button)

        self.rotate_button = QPushButton("Rotate Image")
        self.rotate_button.clicked.connect(self.rotate_image)
        self.rotate_button.setEnabled(False)
        self.rotate_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.rotate_button)

        self.pin_button = QPushButton("Place Pins")
        self.pin_button.clicked.connect(self.place_pins)
        self.pin_button.setEnabled(False)
        self.pin_button.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.pin_button)

        self.submit_pins_button = QPushButton("Submit Pins")
        self.submit_pins_button.clicked.connect(self.submit_pins)
        self.submit_pins_button.setEnabled(False)
        self.submit_pins_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.submit_pins_button)

        self.calibrate_button = QPushButton("Calibrate Ruler")
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.calibrate_button.setEnabled(False)
        self.calibrate_button.setStyleSheet("QPushButton { background-color: #009688; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.calibrate_button)

        self.submit_calibration_button = QPushButton("Submit Calibration Points")
        self.submit_calibration_button.clicked.connect(self.submit_calibration_points)
        self.submit_calibration_button.setEnabled(False)
        self.submit_calibration_button.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.submit_calibration_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setEnabled(False)
        self.reset_button.setStyleSheet("QPushButton { background-color: #E91E63; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.reset_button)

        self.calculate_pitch_button = QPushButton("Calculate Pitch")
        self.calculate_pitch_button.clicked.connect(self.calculate_pitch)
        self.calculate_pitch_button.setEnabled(False)
        self.calculate_pitch_button.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.calculate_pitch_button)

        self.result_label = QLabel("Results will be displayed here.")
        self.result_label.setStyleSheet("QLabel { font-size: 14px; color: #333; }")
        self.control_layout.addWidget(self.result_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { font-size: 14px; }")
        self.control_layout.addWidget(self.progress_bar)

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

        # Connect mouse events
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)
        self.image_view.scene.sigMouseMoved.connect(self.on_mouse_move)

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

        # Enable line drawing and pin placement
        self.line_button.setEnabled(True)
        self.result_label.setText("Image loaded. Click 'Draw Line on Ruler' to align the ruler.")

    def display_image(self, image):
        # Display the image in PyQtGraph
        self.image_view.setImage(np.rot90(image, k=-1))  # Rotate to correct orientation
        self.image_view.getView().invertY(False)  # Ensure y-axis is not inverted

    def start_line_drawing(self):
        # Clear previous line points
        self.line_points = []
        self.red_line.clear()

        # Enable line drawing
        self.result_label.setText("Click to set the first point of the line.")
        self.dragging = True

    def on_mouse_click(self, event):
        if self.dragging:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            if len(self.line_points) == 0:
                # First click: start the line
                self.line_points.append((x, y))
                self.result_label.setText("First point set. Move the mouse to preview the line.")
            elif len(self.line_points) == 1:
                # Second click: end the line
                self.line_points.append((x, y))
                self.dragging = False

                # Draw the final line
                self.red_line.setData(
                    x=[self.line_points[0][0], self.line_points[1][0]],
                    y=[self.line_points[0][1], self.line_points[1][1]],
                    connect='all'
                )

                # Enable rotation
                self.rotate_button.setEnabled(True)
                self.result_label.setText("Line drawn. Click 'Rotate Image' to align the ruler.")

    def on_mouse_move(self, event):
        if self.dragging and len(self.line_points) == 1:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event)
            x, y = int(pos.x()), int(pos.y())

            # Dynamically update the line from the first point to the current mouse position
            self.red_line.setData(
                x=[self.line_points[0][0], x],
                y=[self.line_points[0][1], y],
                connect='all'
            )

    def rotate_image(self):
        if len(self.line_points) != 2:
            QMessageBox.critical(self, "Error", "Please draw a line first.")
            return

        # Calculate the angle of the line relative to the x-axis
        (x1, y1), (x2, y2) = self.line_points
        self.rotation_angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

        # Rotate the image to make the line parallel to the x-axis
        center = (self.image_rgb.shape[1] // 2, self.image_rgb.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, -self.rotation_angle, 1.0)
        self.rotated_image = cv2.warpAffine(self.image_rgb, rotation_matrix, (self.image_rgb.shape[1], self.image_rgb.shape[0]))

        # Display the rotated image
        self.display_image(self.rotated_image)

        # Enable pin placement
        self.pin_button.setEnabled(True)
        self.result_label.setText("Image rotated. Click 'Place Pins' to proceed.")

    def place_pins(self):
        # Create a QInputDialog
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Number of Pins")
        dialog.setLabelText("Enter the number of pins:")
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setIntMinimum(1)  # Set the minimum value to 1
        dialog.setIntValue(1)  # Set the default value to 1

        # Show the dialog and get the result
        ok = dialog.exec()
        if ok:
            num_pins = dialog.intValue()
            self.num_pins = num_pins
            self.pin_coordinates = []
            self.pin_scatter.clear()  # Clear previous pins

            # Enable pin placement
            self.result_label.setText(f"Click on the image to place {self.num_pins} pins.")
            self.image_view.scene.sigMouseClicked.connect(self.on_pin_click)

    def on_pin_click(self, event):
        if len(self.pin_coordinates) < self.num_pins:
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())
            self.pin_coordinates.append((x, y))
            self.pin_scatter.addPoints([x], [y])  # Add visual marker
            self.result_label.setText(f"Pin {len(self.pin_coordinates)} placed at ({x}, {y}).")

            if len(self.pin_coordinates) == self.num_pins:
                self.result_label.setText("All pins placed. Click 'Submit Pins' to proceed.")
                self.submit_pins_button.setEnabled(True)

    def submit_pins(self):
        # Disable pin placement
        self.image_view.scene.sigMouseClicked.disconnect(self.on_pin_click)

        # Enable calibration
        self.result_label.setText("Pins submitted. Now select two calibration points.")
        self.calibrate_button.setEnabled(True)

    def start_calibration(self):
        # Clear previous calibration points
        self.calibration_points = []
        self.calibration_scatter.clear()

        # Enable calibration point selection
        self.result_label.setText("Click on the image to select two calibration points on the ruler.")
        self.image_view.scene.sigMouseClicked.connect(self.on_calibration_click)

    def on_calibration_click(self, event):
        if len(self.calibration_points) < 2:
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())
            self.calibration_points.append((x, y))
            self.calibration_scatter.addPoints([x], [y])  # Add visual marker
            self.result_label.setText(f"Calibration point {len(self.calibration_points)} placed at ({x}, {y}).")

            if len(self.calibration_points) == 2:
                # Disable further calibration point selection
                self.image_view.scene.sigMouseClicked.disconnect(self.on_calibration_click)
                self.result_label.setText("Two calibration points placed. Click 'Submit Calibration Points' to proceed.")
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

            self.result_label.setText(f"Calibration complete. Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.4f} mm/pixel")

            # Enable pitch calculation and reset calibration
            self.calculate_pitch_button.setEnabled(True)
            self.reset_button.setEnabled(True)

    def calculate_pitch(self):
        if len(self.pin_coordinates) < 2:
            QMessageBox.critical(self, "Error", "At least two pins are required to calculate pitch.")
            return

        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Calibration not done. Please calibrate first.")
            return

        # Calculate pitch distances
        pitch_distances = []
        for i in range(len(self.pin_coordinates) - 1):
            x1, y1 = self.pin_coordinates[i]
            x2, y2 = self.pin_coordinates[i + 1]
            distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            distance_mm = distance_pixels / self.pixel_to_mm_ratio
            pitch_distances.append(distance_mm)

        # Display the results
        result_text = "Pin pitch distances (in mm):\n"
        for i, distance in enumerate(pitch_distances):
            result_text += f"Pin {i+1} to Pin {i+2}: {distance:.2f} mm\n"
        self.result_label.setText(result_text)

    def reset(self):
        # Reset all variables and UI elements
        self.image_path = None
        self.image_rgb = None
        self.rotated_image = None
        self.num_pins = 0
        self.pin_coordinates = []
        self.calibration_points = []
        self.line_points = []
        self.rotation_angle = None
        self.dragging = False

        self.pin_scatter.clear()
        self.calibration_scatter.clear()
        self.red_line.clear()
        self.image_view.clear()

        self.load_button.setEnabled(True)
        self.line_button.setEnabled(False)
        self.rotate_button.setEnabled(False)
        self.pin_button.setEnabled(False)
        self.submit_pins_button.setEnabled(False)
        self.calibrate_button.setEnabled(False)
        self.submit_calibration_button.setEnabled(False)
        self.calculate_pitch_button.setEnabled(False)
        self.reset_button.setEnabled(False)

        self.result_label.setText("Results will be displayed here.")


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec())