# Install required libraries: pip install opencv-python numpy matplotlib pyqt5

import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QInputDialog,
    QProgressBar, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


class PinCalibrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pin Detection and Calibration")
        self.setGeometry(100, 100, 1200, 800)

        # Variables
        self.image_path = None
        self.num_pins = 0
        self.pin_coordinates = []
        self.calibration_points = []
        self.pixel_to_mm_ratio = None

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
        self.control_layout.addWidget(self.load_button)

        self.pin_button = QPushButton("Place Pins")
        self.pin_button.clicked.connect(self.place_pins)
        self.pin_button.setEnabled(False)
        self.control_layout.addWidget(self.pin_button)

        self.submit_pins_button = QPushButton("Submit Pins")
        self.submit_pins_button.clicked.connect(self.submit_pins)
        self.submit_pins_button.setEnabled(False)
        self.control_layout.addWidget(self.submit_pins_button)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate)
        self.calibrate_button.setEnabled(False)
        self.control_layout.addWidget(self.calibrate_button)

        self.calculate_pitch_button = QPushButton("Calculate Pitch")
        self.calculate_pitch_button.clicked.connect(self.calculate_pitch)
        self.calculate_pitch_button.setEnabled(False)
        self.control_layout.addWidget(self.calculate_pitch_button)

        self.result_label = QLabel("Results will be displayed here.")
        self.control_layout.addWidget(self.result_label)

        self.progress_bar = QProgressBar()
        self.control_layout.addWidget(self.progress_bar)

        # Matplotlib figure and canvas for image display
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvas(self.fig)
        self.image_layout.addWidget(self.canvas)

        # Navigation toolbar for zooming and panning
        self.toolbar = NavigationToolbar(self.canvas, self.image_panel)
        self.image_layout.addWidget(self.toolbar)

    def load_image(self):
        # Open file dialog to select an image
        self.image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if not self.image_path:
            return

        # Load the image
        image = cv2.imread(self.image_path)
        if image is None:
            QMessageBox.critical(self, "Error", "Could not load image.")
            return

        # Convert to RGB for Matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Display the image
        self.ax.clear()
        self.ax.imshow(image_rgb)
        self.ax.axis("off")
        self.canvas.draw()

        # Enable pin placement
        self.pin_button.setEnabled(True)
        self.result_label.setText("Image loaded. Enter the number of pins and click 'Place Pins'.")

    def place_pins(self):
        # Get the number of pins
        num_pins, ok = QInputDialog.getInt(self, "Number of Pins", "Enter the number of pins:", min=1)
        if not ok:
            return

        self.num_pins = num_pins
        self.pin_coordinates = []

        # Enable pin placement
        self.result_label.setText(f"Click on the image to place {self.num_pins} pins.")
        self.fig.canvas.mpl_connect("button_press_event", self.on_pin_click)

    def on_pin_click(self, event):
        if len(self.pin_coordinates) < self.num_pins:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                self.pin_coordinates.append((x, y))
                self.ax.plot(x, y, 'ro')  # Mark the pin with a red dot
                self.canvas.draw()
                self.result_label.setText(f"Pin {len(self.pin_coordinates)} placed at ({x:.2f}, {y:.2f}).")

                if len(self.pin_coordinates) == self.num_pins:
                    self.result_label.setText("All pins placed. Click 'Submit Pins' to proceed.")
                    self.submit_pins_button.setEnabled(True)

    def submit_pins(self):
        # Disable pin placement
        self.fig.canvas.mpl_disconnect(self.on_pin_click)

        # Enable calibration
        self.result_label.setText("Pins submitted. Now select two calibration points.")
        self.calibrate_button.setEnabled(True)

    def calibrate(self):
        # Connect the mouse click event to select calibration points
        self.result_label.setText("Click on the image to select two calibration points.")
        self.fig.canvas.mpl_connect("button_press_event", self.on_calibration_click)

    def on_calibration_click(self, event):
        if len(self.calibration_points) < 2:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                self.calibration_points.append((x, y))
                self.ax.plot(x, y, 'bo')  # Mark the calibration point with a blue dot
                self.canvas.draw()
                self.result_label.setText(f"Calibration point {len(self.calibration_points)} placed at ({x:.2f}, {y:.2f}).")

                if len(self.calibration_points) == 2:
                    # Ask for the known distance in millimeters
                    known_distance_mm, ok = QInputDialog.getDouble(self, "Calibration", "Enter the known distance between the two points (in mm):", min=0.1)
                    if not ok:
                        return

                    # Calculate the pixel-to-millimeter ratio
                    (x1, y1), (x2, y2) = self.calibration_points
                    distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    self.pixel_to_mm_ratio = distance_pixels / known_distance_mm
                    self.result_label.setText(f"Calibration complete. Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.4f} mm/pixel")

                    # Enable pitch calculation
                    self.calculate_pitch_button.setEnabled(True)

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
        result_text = "Pitch distances (in mm):\n"
        for i, distance in enumerate(pitch_distances):
            result_text += f"Pin {i+1} to Pin {i+2}: {distance:.2f} mm\n"
        self.result_label.setText(result_text)


# Custom NavigationToolbar to remove unnecessary buttons
class NavigationToolbar(NavigationToolbar):
    toolitems = [t for t in NavigationToolbar.toolitems if t[0] in ("Home", "Pan", "Zoom", "Save")]


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec_())