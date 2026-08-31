# GUI for Pin Detection with Matplotlib for Image Display
# Install required libraries: pip install torch torchvision opencv-python numpy matplotlib tkinter

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D  # Correct import for Line2D

# Global variables for calibration
calibration_line = None
calibration_start_point = None
calibration_end_point = None

# Step 1: Load a pre-trained Faster R-CNN model
def load_faster_rcnn_model():
    backbone = torchvision.models.resnet50(pretrained=True)
    backbone = torch.nn.Sequential(*list(backbone.children())[:-2])  # Remove the last two layers
    backbone.out_channels = 2048  # Set the number of output channels

    anchor_generator = AnchorGenerator(
        sizes=((32, 64, 128, 256, 512),),
        aspect_ratios=((0.5, 1.0, 2.0),) * 5
    )

    roi_pooler = torchvision.ops.MultiScaleRoIAlign(
        featmap_names=['0'],
        output_size=7,
        sampling_ratio=2
    )

    model = FasterRCNN(
        backbone,
        num_classes=2,  # 1 class (pin) + background
        rpn_anchor_generator=anchor_generator,
        box_roi_pool=roi_pooler
    )

    model.eval()
    return model

# Step 2: Define the function to process a single image
def process_image(image_path, model, pixel_to_mm_ratio):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}.")
        return None, None

    # Preprocess the image for Faster R-CNN
    image_tensor = torchvision.transforms.functional.to_tensor(image).unsqueeze(0)

    # Run Faster R-CNN inference
    with torch.no_grad():
        predictions = model(image_tensor)

    # Extract bounding boxes and labels
    boxes = predictions[0]['boxes'].cpu().numpy()
    labels = predictions[0]['labels'].cpu().numpy()
    scores = predictions[0]['scores'].cpu().numpy()

    # Filter for "pin" class (class ID 1)
    pin_boxes = []
    for box, label, score in zip(boxes, labels, scores):
        if label == 1 and score > 0.5:  # Class ID 1 is "pin"
            pin_boxes.append(box)

    # Calculate pin pitch in millimeters
    pin_pitch_mm = None
    if len(pin_boxes) >= 2:
        pin_boxes = sorted(pin_boxes, key=lambda x: x[0])  # Sort by x-coordinate
        x1_center = (pin_boxes[0][0] + pin_boxes[0][2]) / 2
        y1_center = (pin_boxes[0][1] + pin_boxes[0][3]) / 2
        x2_center = (pin_boxes[1][0] + pin_boxes[1][2]) / 2
        y2_center = (pin_boxes[1][1] + pin_boxes[1][3]) / 2
        pin_pitch_pixels = np.sqrt((x2_center - x1_center)**2 + (y2_center - y1_center)**2)
        pin_pitch_mm = pin_pitch_pixels * pixel_to_mm_ratio

    # Draw bounding boxes on the image
    for box in pin_boxes:
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, "Pin", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    return image, pin_pitch_mm

# Step 3: Define the GUI
class PinDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pin Detection with Matplotlib for Image Display")
        self.image_paths = []
        self.pixel_to_mm_ratio = None

        # Load the Faster R-CNN model
        self.model = load_faster_rcnn_model()

        # Create GUI elements
        self.label = tk.Label(root, text="Select images of the connector:")
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="Select Images", command=self.select_images)
        self.select_button.pack(pady=10)

        self.calibrate_button = tk.Button(root, text="Calibrate", command=self.calibrate)
        self.calibrate_button.pack(pady=10)

        self.process_button = tk.Button(root, text="Process Images", command=self.process_images)
        self.process_button.pack(pady=10)

        self.result_label = tk.Label(root, text="Results will be displayed here.")
        self.result_label.pack(pady=10)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        # Add Matplotlib navigation toolbar for zooming
        self.toolbar = NavigationToolbar2Tk(self.canvas, root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()

        # Variables for calibration
        self.calibration_line = None
        self.calibration_start_point = None
        self.calibration_end_point = None

    def select_images(self):
        self.image_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if self.image_paths:
            self.label.config(text=f"{len(self.image_paths)} images selected.")

    def calibrate(self):
        if not self.image_paths:
            self.result_label.config(text="No images selected.")
            return

        # Load the first image for calibration
        image = cv2.imread(self.image_paths[0])
        if image is None:
            self.result_label.config(text="Error: Could not load image.")
            return

        # Convert the image to RGB for Matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Display the image in Matplotlib
        self.ax.clear()
        self.ax.imshow(image_rgb)
        self.ax.set_title("Draw a Line for Calibration (Click and Drag)")
        self.ax.axis("off")
        self.canvas.draw()

        # Connect the mouse event handler
        self.calibration_line = None
        self.calibration_start_point = None
        self.calibration_end_point = None
        self.fig.canvas.mpl_connect("button_press_event", self.on_press)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)

    def on_press(self, event):
        # Record the starting point of the line
        self.calibration_start_point = (event.xdata, event.ydata)

    def on_release(self, event):
        # Record the ending point of the line
        self.calibration_end_point = (event.xdata, event.ydata)

        # Draw the line on the image
        if self.calibration_start_point and self.calibration_end_point:
            x1, y1 = self.calibration_start_point
            x2, y2 = self.calibration_end_point
            if self.calibration_line:
                self.calibration_line.remove()  # Remove the previous line
            self.calibration_line = Line2D([x1, x2], [y1, y2], color="r", linewidth=2)
            self.ax.add_line(self.calibration_line)
            self.canvas.draw()

            # Ask the user for the known length in millimeters
            length_mm = simpledialog.askfloat("Calibration", "Enter the known length of the line (in mm):")
            if length_mm is None or length_mm <= 0:
                self.result_label.config(text="Error: Invalid length.")
                return

            # Calculate the pixel-to-millimeter ratio
            length_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self.pixel_to_mm_ratio = length_mm / length_pixels
            self.result_label.config(text=f"Calibration complete. Pixel-to-mm ratio: {self.pixel_to_mm_ratio:.4f} mm/pixel")

    def process_images(self):
        if not self.image_paths:
            self.result_label.config(text="No images selected.")
            return

        if self.pixel_to_mm_ratio is None:
            self.result_label.config(text="Error: Calibration not done.")
            return

        self.ax.clear()
        self.ax.set_title("Processed Images")
        self.ax.axis("off")

        for i, image_path in enumerate(self.image_paths):
            processed_image, pin_pitch_mm = process_image(image_path, self.model, self.pixel_to_mm_ratio)
            if processed_image is not None:
                processed_image_rgb = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
                self.ax.imshow(processed_image_rgb)
                self.canvas.draw()
                if pin_pitch_mm is not None:
                    self.result_label.config(text=f"Pin pitch in image {i+1}: {pin_pitch_mm:.2f} mm")
                else:
                    self.result_label.config(text=f"No pins detected in image {i+1}.")
                self.root.update()
                self.root.after(2000)  # Pause for 2 seconds between images

# Step 4: Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = PinDetectionApp(root)
    root.mainloop()