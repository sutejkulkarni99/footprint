import sys
import cv2
import numpy as np
from scipy.spatial import KDTree
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QInputDialog, QMessageBox,
    QTextEdit, QGridLayout
)
from PySide6.QtGui import QImage, QPixmap, QTextCursor
from PySide6.QtCore import Qt
import pyqtgraph as pg
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import cadquery as cq
from cadquery import exporters

def create_ipc7351_footprint(filename, footprint_name, num_pins, pitch,
                            pin_diameter, border_width, border_height,
                            component_type="Through-Hole", pin_rows=None):
    if not isinstance(filename, str):
        raise ValueError("Filename must be a string.")
    if not isinstance(footprint_name, str):
        raise ValueError("Footprint name must be a string.")
    if num_pins <= 0 or not isinstance(num_pins, int):
        raise ValueError("Number of pins must be a positive integer.")
    if pitch <= 0:
        raise ValueError("Pitch must be a positive number.")
    if pin_diameter <= 0:
        raise ValueError("Pin diameter must be a positive number.")
    if border_width <= 0 or border_height <= 0:
        raise ValueError("Border dimensions must be positive numbers.")
    if component_type not in ["SMD", "Through-Hole"]:
        raise ValueError("Invalid component type")
    if not pin_rows or len(pin_rows) == 0:
        raise ValueError("Pin rows must be provided")

    pad_type = "smd" if component_type == "SMD" else "thru_hole"
    content = f"""(module {footprint_name} (layer F.Cu) (tedit 12345678)
  (descr "IPC-7351 compliant footprint")
  (tags "connector")
  (attr {component_type.lower()})
  (fp_text reference J1 (at 0 {-border_height/2 - 2}) (layer F.SilkS)
    (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value {footprint_name} (at 0 {border_height/2 + 2}) (layer F.Fab)
    (effects (font (size 1 1) (thickness 0.15))))"""

    # Silkscreen outline
    content += f"""
  (fp_line (start {-border_width/2} {-border_height/2}) (end {border_width/2} {-border_height/2}) (layer F.SilkS) (width 0.15))
  (fp_line (start {border_width/2} {-border_height/2}) (end {border_width/2} {border_height/2}) (layer F.SilkS) (width 0.15))
  (fp_line (start {border_width/2} {border_height/2}) (end {-border_width/2} {border_height/2}) (layer F.SilkS) (width 0.15))
  (fp_line (start {-border_width/2} {border_height/2}) (end {-border_width/2} {-border_height/2}) (layer F.SilkS) (width 0.15))"""

    # Pads
    pin_number = 1
    for row_idx, row in enumerate(pin_rows):
        for i, (x, y) in enumerate(row):
            pad_x = i * pitch - (len(row) - 1) * pitch / 2
            pad_y = row_idx * pitch
            content += f"""
  (pad {pin_number} {pad_type} rect (at {pad_x} {pad_y}) (size 1.5 1.5) (layers *.Cu *.Mask F.SilkS))"""
            pin_number += 1

    content += "\n)"
    with open(filename, "w") as f:
        f.write(content)
    print(f"Footprint saved as {filename}")

class PinCalibrationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCB Footprint Generator")
        self.setGeometry(100, 100, 1280, 720)
        
        # State variables
        self.image_path = None
        self.image_rgb = None
        self.original_image = None
        self.edges = None
        self.edge_points = None
        self.edge_kdtree = None
        self.pin_rows = []
        self.current_row = []
        self.square_points = []
        self.calibration_points = []
        self.lasso_points = []
        self.homography_matrix = None
        self.pixel_to_mm_ratio = None
        self.rotation_correction = True
        
        # UI Setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        
        # Control Panel
        self.control_panel = QWidget()
        self.control_layout = QGridLayout(self.control_panel)
        self.layout.addWidget(self.control_panel, stretch=1)
        
        # Image Display
        self.image_panel = QWidget()
        self.image_layout = QVBoxLayout(self.image_panel)
        self.layout.addWidget(self.image_panel, stretch=3)
        
        # Widgets
        self.create_widgets()
        self.setup_connections()
        
        # Visualization items
        self.image_view = pg.ImageView()
        self.image_layout.addWidget(self.image_view)
        self.pin_scatter = pg.ScatterPlotItem(pen='r', symbol='o', size=10)
        self.calibration_scatter = pg.ScatterPlotItem(pen='b', symbol='x', size=10)
        self.square_scatter = pg.ScatterPlotItem(pen='g', symbol='s', size=10)
        self.image_view.getView().addItem(self.pin_scatter)
        self.image_view.getView().addItem(self.calibration_scatter)
        self.image_view.getView().addItem(self.square_scatter)
        
    def create_widgets(self):
        buttons = [
            ("Load Image", self.load_image),
            ("Select Square", self.start_selecting_square),
            ("Calibrate Ruler", self.start_calibration),
            ("Select Pins", self.start_selecting_pins),
            ("Add Row", self.add_new_row),
            ("Calculate Pitch", self.calculate_pitch),
            ("Generate Drawing", self.generate_2d_drawing),
            ("Generate STEP", self.generate_step_file_dialog),
            ("Generate Footprint", self.generate_footprint),
            ("Reset", self.reset)
        ]
        
        for i, (text, handler) in enumerate(buttons):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn.setFixedSize(150, 40)
            self.control_layout.addWidget(btn, i, 0)
            
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.control_layout.addWidget(self.result_text, len(buttons)+1, 0)

    def setup_connections(self):
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click)
        self.image_view.scene.sigMouseMoved.connect(self.on_mouse_move)

    # --------------------- Core Functionality ---------------------
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.jpg *.png)")
        if not path: return
        
        self.original_image = cv2.imread(path)
        if self.original_image is None:
            QMessageBox.critical(self, "Error", "Failed to load image")
            return
        
        # Edge detection
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        self.edges = cv2.Canny(gray, 100, 200)
        self.edge_points = np.column_stack(np.where(self.edges > 0))
        self.edge_kdtree = KDTree(self.edge_points) if len(self.edge_points) > 0 else None
        
        # Prepare display image
        self.image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        edges_rgb = cv2.cvtColor(self.edges, cv2.COLOR_GRAY2RGB)
        edges_rgb[self.edges > 0] = [0, 255, 0]
        self.display_image(cv2.addWeighted(self.image_rgb, 0.7, edges_rgb, 0.3, 0))
        self.update_result("Image loaded. Select square corners first.")

    def display_image(self, image):
        if self.rotation_correction:
            self.image_view.setImage(np.rot90(image, k=-1))
        else:
            self.image_view.setImage(image)
        self.image_view.getView().invertY(False)

    def adjust_coordinates(self, x, y):
        """Convert display coordinates to original image space with perspective correction"""
        if self.rotation_correction and self.image_rgb is not None:
            h, w = self.image_rgb.shape[:2]
            x_orig = h - y - 1
            y_orig = x
        else:
            x_orig, y_orig = x, y

        if self.homography_matrix is not None:
            src_pt = np.array([[[x_orig, y_orig]]], dtype="float32")
            dst_pt = cv2.perspectiveTransform(src_pt, self.homography_matrix)
            return dst_pt[0][0]
        return (x_orig, y_orig)

    def on_mouse_click(self, event):
        pos = self.image_view.getView().mapSceneToView(event.pos())
        x, y = int(pos.x()), int(pos.y())
        x_corr, y_corr = self.adjust_coordinates(x, y)

        if self.selecting_square:
            self.handle_square_click(x_corr, y_corr)
        elif self.selecting_calibration:
            self.handle_calibration_click(x_corr, y_corr)
        elif self.selecting_pins:
            self.handle_pin_click(x_corr, y_corr)

    def handle_square_click(self, x, y):
        self.square_points.append((x, y))
        self.square_scatter.addPoints([x], [y])
        
        if len(self.square_points) == 4:
            self.calculate_homography()

    def calculate_homography(self):
        src_points = np.array(self.square_points, dtype="float32")
        size_mm, ok = QInputDialog.getDouble(self, "Square Size", 
                                           "Enter square side length (mm):",
                                           50.0, 1.0, 1000.0, 2)
        if not ok: return
        
        dst_points = np.array([
            [0, 0],
            [size_mm, 0],
            [size_mm, size_mm],
            [0, size_mm]
        ], dtype="float32")
        
        self.homography_matrix, _ = cv2.findHomography(src_points, dst_points)
        self.update_result(f"Perspective correction applied\nHomography matrix:\n{self.homography_matrix}")

    def handle_calibration_click(self, x, y):
        self.calibration_points.append((x, y))
        if len(self.calibration_points) == 2:
            self.calculate_calibration()

    def calculate_calibration(self):
        pt1, pt2 = np.array(self.calibration_points, dtype="float32")
        distance_px = np.linalg.norm(pt2 - pt1)
        distance_mm, ok = QInputDialog.getDouble(self, "Calibration",
                                               "Enter known distance (mm):",
                                               100.0, 1.0, 1000.0, 2)
        if not ok: return
        
        self.pixel_to_mm_ratio = distance_mm / distance_px
        self.update_result(f"Calibration complete\n1px = {self.pixel_to_mm_ratio:.4f}mm")

    def handle_pin_click(self, x, y):
        self.current_row.append((x, y))
        color = self.row_colors[len(self.pin_rows) % len(self.row_colors)]
        self.pin_scatter.addPoints([x], [y], pen=color, brush=color)
        self.update_result(f"Pin {len(self.current_row)} placed at ({x:.2f}, {y:.2f}) mm")

    def calculate_border_width(self):
        if not self.pin_rows: return 10.0
        all_x = [pin[0] for row in self.pin_rows for pin in row]
        return max((max(all_x) - min(all_x)) + 5.0, 10.0)

    def calculate_border_height(self):
        if not self.pin_rows: return 10.0
        all_y = [pin[1] for row in self.pin_rows for pin in row]
        return max((max(all_y) - min(all_y)) + 5.0, 10.0)

    def generate_footprint(self):
        try:
            border_w = self.calculate_border_width()
            border_h = self.calculate_border_height()
            
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Footprint",
                                                     "", "KiCad Files (*.kicad_mod)")
            if not file_path: return
            
            create_ipc7351_footprint(
                file_path, "Generated_Footprint",
                sum(len(row) for row in self.pin_rows),
                2.54, 1.0, border_w, border_h,
                "Through-Hole", self.pin_rows
            )
            self.update_result(f"Footprint saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Generation failed: {str(e)}")

    # --------------------- Helper Methods ---------------------
    def update_result(self, text):
        self.result_text.append(text)
        self.result_text.moveCursor(QTextCursor.End)

    def reset(self):
        self.image_view.clear()
        self.pin_scatter.clear()
        self.calibration_scatter.clear()
        self.square_scatter.clear()
        self.pin_rows = []
        self.current_row = []
        self.square_points = []
        self.calibration_points = []
        self.homography_matrix = None
        self.pixel_to_mm_ratio = None
        self.update_result("System reset")

        def generate_2d_drawing(self):
        """
        Generate a 2D CAD drawing with accurate measurements for the border and pins.
        """
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

        # Plot the pins
        hole_diameter = 1.0  # 1.0mm diameter
        hole_radius = hole_diameter / 2

        # Align the first pin of each row in a straight line
        first_pin_x = self.pin_rows[0][0][0] / self.pixel_to_mm_ratio  # X position of the first pin in the first row

        for row_idx, row in enumerate(self.pin_rows):
            color = self.row_colors[row_idx % len(self.row_colors)]
            y_position = row[0][1] / self.pixel_to_mm_ratio  # Convert to mm

            # Align the first pin of each row to the same X position
            x_positions = [first_pin_x + (pin[0] - row[0][0]) / self.pixel_to_mm_ratio for pin in row]

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
                pitch = (x2 - x1)  # Pitch in mm
                mid_x = (x1 + x2) / 2

                # Draw a dashed line for the pitch
                ax.plot([x1, x2], [y_position - 1.5 * hole_radius, y_position - 1.5 * hole_radius], 
                        color=color, linestyle='--')

                # Add pitch text below the dashed line
                ax.text(mid_x, y_position - 2.5 * hole_radius, f'PITCH {pitch:.2f}mm', 
                        fontsize=8, ha='center', va='top', color=color)

        # Add the polygon border (if defined)
        if len(self.lasso_points) > 2:
            # Transform border points using homography and pixel-to-mm ratio
            transformed_border_points = self.transform_points(self.lasso_points)

            # Create a polygon from the transformed points
            polygon = Polygon(transformed_border_points, edgecolor='y', facecolor='none', linestyle='--')
            ax.add_patch(polygon)

            # Add dimensions for the polygon border
            for i in range(len(transformed_border_points)):
                x1, y1 = transformed_border_points[i]
                x2, y2 = transformed_border_points[(i + 1) % len(transformed_border_points)]
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)  # Length in mm
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2

                # Draw dimension lines
                ax.plot([x1, x2], [y1, y2], color='k', linestyle='-', linewidth=0.5)
                ax.text(mid_x, mid_y, f'{length:.2f}mm', fontsize=8, ha='center', va='bottom', color='k')

        # Set plot limits with extra padding to avoid text overlap
        all_x = [pin[0] / self.pixel_to_mm_ratio for row in self.pin_rows for pin in row]
        all_y = [pin[1] / self.pixel_to_mm_ratio for row in self.pin_rows for pin in row]

        # Include the polygon border in the plot limits
        if len(self.lasso_points) > 2:
            polygon_x = [x / self.pixel_to_mm_ratio for x, y in self.lasso_points]
            polygon_y = [y / self.pixel_to_mm_ratio for x, y in self.lasso_points]
            all_x.extend(polygon_x)
            all_y.extend(polygon_y)

        # Add extra padding to the plot limits
        padding = 5  # 5mm padding
        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)

        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)

        # Add labels
        ax.set_xlabel("X Position (mm)")
        ax.set_ylabel("Y Position (mm)")
        ax.set_title("2D CAD Drawing of Pin Holes and Border")

        # Save the plot as a vector image (SVG) or high-resolution raster image
        file_path, _ = QFileDialog.getSaveFileName(self, "Save 2D Drawing", "", "Vector Image (*.svg);;Image Files (*.jpg *.png)")
        if file_path:
            if file_path.endswith('.svg'):
                plt.savefig(file_path, format='svg', bbox_inches='tight')  # Save as SVG
            else:
                plt.savefig(file_path, dpi=300, bbox_inches='tight')  # Save as high-res raster image
            plt.close()  # Close the figure to free memory
            self.update_result_text(f"2D CAD drawing saved to {file_path}")
        else:
            plt.close()  # Close the figure if the user cancels
            self.update_result_text("2D CAD drawing not saved.")

    def transform_points(self, points):
        """
        Transform points using the homography matrix and pixel-to-mm ratio.
        """
        if self.homography_matrix is None or self.pixel_to_mm_ratio is None:
            return points  # Return original points if calibration is not done

        # Convert points to a numpy array
        points = np.array(points, dtype="float32").reshape(-1, 1, 2)

        # Apply homography transformation
        transformed_points = cv2.perspectiveTransform(points, self.homography_matrix)

        # Convert pixel coordinates to millimeters
        transformed_points = transformed_points.reshape(-1, 2) / self.pixel_to_mm_ratio

        return transformed_points.tolist()

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

    def start_polygon_selection(self):
        """
        Start the process of polygon selection with snapping.
        """
        # Clear previous polygon points
        self.lasso_points = []
        self.lasso_scatter = pg.ScatterPlotItem(pen='y', symbol='o', size=10, brush='y')  # Scatter plot for polygon points
        self.image_view.getView().addItem(self.lasso_scatter)  # Add scatter plot to the view
        self.selecting_lasso = True
        self.selecting_square = False
        self.selecting_calibration = False
        self.selecting_pins = False
        self.selecting_mounting_hole = False
        self.selecting_border = False

        # Clear previous lines
        self.polygon_lines = []

        # Change button text
        self.add_lasso_button.setText("Submit Polygon")
        self.add_lasso_button.clicked.disconnect()
        self.add_lasso_button.clicked.connect(self.submit_polygon)

        # Enable the reset polygon button
        self.reset_polygon_button.setEnabled(True)

        # Disconnect any previous connections to avoid multiple triggers
        try:
            self.image_view.scene.sigMouseClicked.disconnect()
        except TypeError:
            pass  # Ignore if no connections exist

        # Connect the mouse click event
        self.image_view.scene.sigMouseClicked.connect(self.on_mouse_click_polygon)

        self.update_result_text("Left-click to add points with edge snapping. Right-click to finish.")

    def on_mouse_click_polygon(self, event):
        """
        Handle mouse clicks for polygon selection with snapping.
        """
        if self.selecting_lasso:
            # Get the position relative to the view and map it to the scene
            pos = self.image_view.getView().mapSceneToView(event.pos())
            x, y = int(pos.x()), int(pos.y())

            # Snap the point to the nearest edge
            snapped_point = self.snap_to_edge(x, y)
            if snapped_point is not None:
                x, y = snapped_point

            # Add the point to the polygon points
            self.lasso_points.append((x, y))

            # Update the scatter plot with all points
            self.lasso_scatter.setData([p[0] for p in self.lasso_points], [p[1] for p in self.lasso_points])

            # Draw lines between all points to visualize the polygon
            if len(self.lasso_points) > 1:
                # Remove previous lines
                for line in self.polygon_lines:
                    self.image_view.getView().removeItem(line)
                self.polygon_lines = []

                # Draw all connecting lines
                for i in range(len(self.lasso_points) - 1):
                    x1, y1 = self.lasso_points[i]
                    x2, y2 = self.lasso_points[i + 1]
                    line = pg.PlotCurveItem([x1, x2], [y1, y2], pen='y')
                    self.image_view.getView().addItem(line)
                    self.polygon_lines.append(line)

            self.update_result_text(f"Polygon point {len(self.lasso_points)} placed at ({x}, {y}).")

            # If the user right-clicks, complete the polygon
            if event.button() == Qt.RightButton:
                self.submit_polygon()

    def on_mouse_move(self, pos):
        """
        Handle mouse movement events during polygon selection.
        """
        if self.selecting_lasso and len(self.lasso_points) > 0:
            # Get the position relative to the view and map it to the scene
            scene_pos = self.image_view.getView().mapSceneToView(pos)
            x, y = int(scene_pos.x()), int(scene_pos.y())

            # Snap the point to the nearest edge
            snapped_point = self.snap_to_edge(x, y)
            if snapped_point is not None:
                x, y = snapped_point

            # Draw a temporary line from the last point to the current mouse position
            x1, y1 = self.lasso_points[-1]
            if self.lasso_line:
                self.image_view.getView().removeItem(self.lasso_line)
            self.lasso_line = pg.PlotCurveItem([x1, x], [y1, y], pen='y')
            self.image_view.getView().addItem(self.lasso_line)

    def snap_to_edge(self, x, y):
        """
        Snap the point (x, y) to the nearest edge using KDTree.
        """
        if self.edge_kdtree is None:
            return None

        # Define a search radius (10 pixels)
        search_radius = 10

        # Query the KDTree for the nearest edge point within the radius
        distance, index = self.edge_kdtree.query((y, x), distance_upper_bound=search_radius)

        if index < len(self.edge_points):
            # Return the snapped point (x, y)
            snapped_y, snapped_x = self.edge_points[index]
            return snapped_x, snapped_y
        else:
            return None  # No edge found within the radius

    def submit_polygon(self):
        """
        Submit the polygon selection.
        """
        if len(self.lasso_points) < 3:
            QMessageBox.critical(self, "Error", "At least 3 points are required to create a polygon.")
            return

        # Close the polygon by connecting the last point to the first point
        x1, y1 = self.lasso_points[-1]
        x2, y2 = self.lasso_points[0]
        line = pg.PlotCurveItem([x1, x2], [y1, y2], pen='y')
        self.image_view.getView().addItem(line)
        self.polygon_lines.append(line)

        # Disable polygon selection
        self.selecting_lasso = False
        self.image_view.scene.sigMouseClicked.disconnect(self.on_mouse_click_polygon)

        # Change button text back
        self.add_lasso_button.setText("Polygon Select")
        self.add_lasso_button.clicked.disconnect()
        self.add_lasso_button.clicked.connect(self.start_polygon_selection)

        # Disable the reset polygon button
        self.reset_polygon_button.setEnabled(False)

        self.update_result_text("Polygon selection submitted.")

    def reset_polygon(self):
        """
        Reset the polygon selection by clearing all points and lines.
        """
        # Clear the polygon points
        self.lasso_points = []

        # Clear the scatter plot for polygon points
        if self.lasso_scatter:
            self.image_view.getView().removeItem(self.lasso_scatter)
            self.lasso_scatter = None

        # Clear all polygon lines
        for line in self.polygon_lines:
            self.image_view.getView().removeItem(line)
        self.polygon_lines = []

        # Clear the temporary lasso line
        if self.lasso_line:
            self.image_view.getView().removeItem(self.lasso_line)
        self.lasso_line = None

        # Reset the button text and state
        self.add_lasso_button.setText("Polygon Select")
        self.add_lasso_button.clicked.disconnect()
        self.add_lasso_button.clicked.connect(self.start_polygon_selection)

        # Disable the reset polygon button
        self.reset_polygon_button.setEnabled(False)

        self.update_result_text("Polygon selection reset. Click 'Polygon Select' to start over.")

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
        self.generate_footprint_button.setEnabled(False)  # Disable footprint generation
        self.add_lasso_button.setEnabled(False)
        self.reset_polygon_button.setEnabled(False)

        self.update_result_text("Results will be displayed here.")

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PinCalibrationApp()
    window.show()
    sys.exit(app.exec())