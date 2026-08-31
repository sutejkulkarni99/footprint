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
        self.setWindowTitle("Pin Pitch Measurement Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Variables
        self.image_path = None
        self.image_rgb = None
        self.pin_coordinates = []  # Stores pin tip coordinates
        self.calibration_points = []  # Stores ruler calibration points
        self.pixel_to_mm_ratio = None  # Pixel-to-mm conversion factor
        self.rotation_angle = None  # Angle for image alignment
        self.rotated_image = None  # Stores the rotated image

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

        self.calibrate_button = QPushButton("Calibrate Ruler")
        self.calibrate_button.clicked.connect(self.start_calibration)
        self.calibrate_button.setEnabled(False)
        self.calibrate_button.setStyleSheet("QPushButton { background-color: #FFC107; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.calibrate_button)

        self.place_pins_button = QPushButton("Place Pin Tips")
        self.place_pins_button.clicked.connect(self.place_pins)
        self.place_pins_button.setEnabled(False)
        self.place_pins_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.place_pins_button)

        self.calculate_pitch_button = QPushButton("Calculate Pin Pitch")
        self.calculate_pitch_button.clicked.connect(self.calculate_pitch)
        self.calculate_pitch_button.setEnabled(False)
        self.calculate_pitch_button.setStyleSheet("QPushButton { background-color: #E91E63; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.calculate_pitch_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setEnabled(False)
        self.reset_button.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-size: 16px; padding: 10px; }")
        self.control_layout.addWidget(self.reset_button)

        self.result_label = QLabel("Results will be displayed here.")
        self.result_label.setStyleSheet("QLabel { font-size: 14px; color: #333; }")
        self.control_layout.addWidget(self.result_label)

        # PyQtGraph image display
        self.image_view = pg.ImageView()
        self.image_layout.addWidget(self.image_view)

        # Scatter plot items for pins and calibration points
        self.pin_scatter = pg.ScatterPlotItem(pen='r', symbol='o', size=10, brush='r')
        self.calibration_scatter = pg.ScatterPlotItem(pen='b', symbol='x', size=10, brush='b')
        self.image_view.getView().addItem(self.pin_scatter)
        self.image_view.getView().addItem(self.calibration_scatter)

    def load_image(self):
        self.image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if not self.image_path:
            return
        self.original_image = cv2.imread(self.image_path)
        if self.original_image is None:
            QMessageBox.critical(self, "Error", "Could not load image.")
            return
        self.image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        self.display_image(self.image_rgb)
        self.calibrate_button.setEnabled(True)
        self.place_pins_button.setEnabled(True)
        self.result_label.setText("Image loaded. Click 'Calibrate Ruler' to set the pixel-to-mm ratio.")

    def display_image(self, image):
        self.image_view.setImage(np.rot90(image, k=-1))
        self.image_view.getView().invertY(False)

    def start_calibration(self):
        self.calibration_points = []
        self.calibration_scatter.clear()
        self.result_label.setText("Click on the image to select two calibration points on the ruler.")
        self.image_view.scene.sigMouseClicked.connect(self.on_calibration_click)

    def on_calibration_click(self, event):
        if len(self.calibration_points) < 2:
            pos = event.scenePos()
            x, y = int(pos.x()), int(pos.y())
            self.calibration_points.append((x, y))
            self.calibration_scatter.addPoints([x], [y])
            self.result_label.setText(f"Calibration point {len(self.calibration_points)} placed at ({x}, {y}).")
            if len(self.calibration_points) == 2:
                self.image_view.scene.sigMouseClicked.disconnect(self.on_calibration_click)
                self.prompt_for_known_distance()

    def prompt_for_known_distance(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Calibration")
        dialog.setLabelText("Enter the known distance between the two points (in mm):")
        dialog.setInputMode(QInputDialog.DoubleInput)
        dialog.setDoubleMinimum(0.1)
        dialog.setDoubleValue(10.0)
        ok = dialog.exec()
        if ok:
            known_distance_mm = dialog.doubleValue()
            (x1, y1), (x2, y2) = self.calibration_points
            distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self.pixel_to_mm_ratio = distance_pixels / known_distance_mm
            self.rotation_angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            self.rotate_image()
            self.place_pins_button.setEnabled(True)
            self.calculate_pitch_button.setEnabled(True)
            self.reset_button.setEnabled(True)

    def rotate_image(self):
        center = (self.image_rgb.shape[1] // 2, self.image_rgb.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, -self.rotation_angle, 1.0)
        self.rotated_image = cv2.warpAffine(self.image_rgb, rotation_matrix, (self.image_rgb.shape[1], self.image_rgb.shape[0]))
        self.display_image(self.rotated_image)

    def place_pins(self):
        self.pin_coordinates = []
        self.pin_scatter.clear()
        self.result_label.setText("Click on the image to place pin tips.")
        self.image_view.scene.sigMouseClicked.connect(self.on_pin_click)

    def on_pin_click(self, event):
        pos = event.scenePos()
        x, y = int(pos.x()), int(pos.y())
        self.pin_coordinates.append((x, y))
        self.pin_scatter.addPoints([x], [y])
        self.result_label.setText(f"Pin tip {len(self.pin_coordinates)} placed at ({x}, {y}).")

    def calculate_pitch(self):
        if len(self.pin_coordinates) < 2:
            QMessageBox.critical(self, "Error", "At least two pin tips are required to calculate pitch.")
            return
        if self.pixel_to_mm_ratio is None:
            QMessageBox.critical(self, "Error", "Calibration not done. Please calibrate first.")
            return
        x_coords = [x for x, y in self.pin_coordinates]
        x_coords_sorted = sorted(x_coords)
        pitch_distances = []
        for i in range(len(x_coords_sorted) - 1):
            distance_pixels = x_coords_sorted[i + 1] - x_coords_sorted[i]
            distance_mm = distance_pixels / self.pixel_to_mm_ratio
            pitch_distances.append(distance_mm)
        result_text = "Pin pitch distances (in mm):\n"
        for i, distance in enumerate(pitch_distances):
            result_text += f"Pin {i+1} to Pin {i+2}: {distance:.2f} mm\n"
        self.result_label.setText(result_text)

    def reset(self):
        self.image_path = None
        self.image_rgb = None
        self.pin_coordinates = []
        self.calibration_points = []
        self.pixel_to_mm_ratio = None
        self.rotation_angle = None
        self.rotated_image = None
        self.pin_scatter.clear()
        self.calibration_scatter.clear()
        self.image_view.clear()
        self.load_button.setEnabled(True)
        self.calibrate_button.setEnabled(False)
        self.place_pins_button.setEnabled(False)
        self.calculate_pitch_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.result_label.setText("Results will be displayed here.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec())
