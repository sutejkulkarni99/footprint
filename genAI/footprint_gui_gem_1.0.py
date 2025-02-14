import sys
import math
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QFileDialog, QVBoxLayout, QHBoxLayout, QGraphicsView,
                             QGraphicsScene, QInputDialog, QMessageBox)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPointF

class PinPitchMeasurement(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pin Pitch Measurement")

        self.image_path = None
        self.image_pixmap = None
        self.points = []  # Store points: [(x, y, type), ...] where type is 'ruler' or 'pin'
        self.ratio = None
        self.angle = None

        self.image_label = QLabel()
        self.scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.scene)

        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        self.ruler_button = QPushButton("Add Ruler Point")
        self.ruler_button.clicked.connect(lambda: self.add_point('ruler'))
        self.pin_button = QPushButton("Add Pin Point")
        self.pin_button.clicked.connect(lambda: self.add_point('pin'))
        self.measure_button = QPushButton("Measure Pitch")
        self.measure_button.clicked.connect(self.measure_pitch)
        self.clear_button = QPushButton("Clear Points")
        self.clear_button.clicked.connect(self.clear_points)

        hbox = QHBoxLayout()
        hbox.addWidget(self.load_button)
        hbox.addWidget(self.ruler_button)
        hbox.addWidget(self.pin_button)
        hbox.addWidget(self.measure_button)
        hbox.addWidget(self.clear_button)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.graphics_view)
        self.setLayout(vbox)

    def load_image(self):
        file_dialog = QFileDialog(self)
        self.image_path, _ = file_dialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if self.image_path:
            self.image_pixmap = QPixmap(self.image_path)
            self.scene.clear()
            self.scene.addPixmap(self.image_pixmap)
            self.graphics_view.setScene(self.scene)
            self.points = [] # Clear points when loading a new image

    def add_point(self, point_type):
      if self.image_pixmap is None:
          QMessageBox.warning(self, "No Image", "Please load an image first.")
          return

      def mousePressEvent(event):
          scene_pos = self.graphics_view.mapToScene(event.pos())
          x, y = scene_pos.x(), scene_pos.y()
          self.points.append((x, y, point_type))
          self.draw_points()
          self.graphics_view.mousePressEvent = lambda event: QGraphicsView.mousePressEvent(self.graphics_view, event) # Restore default event

      self.graphics_view.mousePressEvent = mousePressEvent

    def draw_points(self):
        self.scene.clear()
        self.scene.addPixmap(self.image_pixmap)
        pen = QPen(Qt.red, 3)
        for x, y, point_type in self.points:
          self.scene.addEllipse(x - 5, y - 5, 10, 10, pen)

    def measure_pitch(self):
      if len([p for p in self.points if p[2]=='ruler']) < 2:
        QMessageBox.warning(self, "Missing Ruler Points", "Please select at least two ruler points.")
        return
      if len([p for p in self.points if p[2]=='pin']) < 2:
        QMessageBox.warning(self, "Missing Pin Points", "Please select at least two pin points.")
        return
      ruler_points = [p[:2] for p in self.points if p[2]=='ruler']
      pin_points = [p[:2] for p in self.points if p[2]=='pin']

      x1, y1 = ruler_points[0]
      x2, y2 = ruler_points[1]

      dpixels = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
      dmm, ok = QInputDialog.getDouble(self, "Enter Ruler Distance", "Distance (mm):", 10.0, 0, 100, 2)
      if not ok:
        return
      self.ratio = dmm / dpixels
      self.angle = math.atan2(y2 - y1, x2 - x1)

      rotated_pin_points = []
      for x, y in pin_points:
          x_rot = x * math.cos(self.angle) - y * math.sin(self.angle)
          y_rot = x * math.sin(self.angle) + y * math.cos(self.angle)
          rotated_pin_points.append(x_rot)
      rotated_pin_points.sort()

      distances = []
      for i in range(len(rotated_pin_points) - 1):
          distance_pixels = rotated_pin_points[i+1] - rotated_pin_points[i]
          distance_mm = distance_pixels * self.ratio
          distances.append(distance_mm)
      
      msg = "Pin Pitch Distances (mm):\n"
      for i, dist in enumerate(distances):
        msg += f"Between Pin {i+1} and {i+2}: {dist:.2f}\n"
      QMessageBox.information(self, "Measurement Results", msg)

    def clear_points(self):
        self.points = []
        self.draw_points()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinPitchMeasurement()
    window.show()
    sys.exit(app.exec())