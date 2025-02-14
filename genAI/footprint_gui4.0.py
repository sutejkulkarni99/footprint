# Enhanced GUI for Pin Detection and Calibration with Free Zooming
# Install required libraries: pip install opencv-python numpy matplotlib tkinter

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

# Global variables
image_path = None
num_pins = 0
pin_coordinates = []
calibration_points = []
pixel_to_mm_ratio = None

# Step 1: Load and display the image
def load_image():
    global image_path, ax, canvas
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not image_path:
        return

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        result_label.config(text="Error: Could not load image.")
        return

    # Convert to RGB for Matplotlib
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Display the image
    ax.clear()
    ax.imshow(image_rgb)
    ax.axis("off")
    canvas.draw()

    # Enable pin selection
    pin_button.config(state=tk.NORMAL)
    result_label.config(text="Image loaded. Enter the number of pins and click 'Place Pins'.")

# Step 2: Place pins on the image
def place_pins():
    global num_pins, pin_coordinates

    # Get the number of pins
    try:
        num_pins = int(simpledialog.askstring("Number of Pins", "Enter the number of pins:"))
        if num_pins <= 0:
            raise ValueError
    except:
        result_label.config(text="Error: Invalid number of pins.")
        return

    # Reset pin coordinates
    pin_coordinates = []

    # Connect the mouse click event to place pins
    result_label.config(text=f"Click on the image to place {num_pins} pins.")
    fig.canvas.mpl_connect("button_press_event", on_pin_click)

# Step 3: Handle pin placement clicks
def on_pin_click(event):
    global pin_coordinates

    if len(pin_coordinates) < num_pins:
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            pin_coordinates.append((x, y))
            ax.plot(x, y, 'ro')  # Mark the pin with a red dot
            canvas.draw()
            result_label.config(text=f"Pin {len(pin_coordinates)} placed at ({x:.2f}, {y:.2f}).")

            if len(pin_coordinates) == num_pins:
                result_label.config(text="All pins placed. Click 'Submit Pins' to proceed.")
                submit_pins_button.config(state=tk.NORMAL)

# Step 4: Submit pins and prepare for calibration
def submit_pins():
    global pin_coordinates

    # Disable pin placement
    fig.canvas.mpl_disconnect(on_pin_click)

    # Enable calibration
    result_label.config(text="Pins submitted. Now select two calibration points.")
    calibrate_button.config(state=tk.NORMAL)

# Step 5: Calibrate using two points
def calibrate():
    global calibration_points, pixel_to_mm_ratio

    # Connect the mouse click event to select calibration points
    result_label.config(text="Click on the image to select two calibration points.")
    fig.canvas.mpl_connect("button_press_event", on_calibration_click)

# Step 6: Handle calibration point clicks
def on_calibration_click(event):
    global calibration_points, pixel_to_mm_ratio

    if len(calibration_points) < 2:
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            calibration_points.append((x, y))
            ax.plot(x, y, 'bo')  # Mark the calibration point with a blue dot
            canvas.draw()
            result_label.config(text=f"Calibration point {len(calibration_points)} placed at ({x:.2f}, {y:.2f}).")

            if len(calibration_points) == 2:
                # Ask for the known distance in millimeters
                known_distance_mm = simpledialog.askfloat("Calibration", "Enter the known distance between the two points (in mm):")
                if known_distance_mm is None or known_distance_mm <= 0:
                    result_label.config(text="Error: Invalid distance.")
                    return

                # Calculate the pixel-to-millimeter ratio
                (x1, y1), (x2, y2) = calibration_points
                distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                pixel_to_mm_ratio = distance_pixels / known_distance_mm
                result_label.config(text=f"Calibration complete. Pixel-to-mm ratio: {pixel_to_mm_ratio:.4f} mm/pixel")

                # Enable pitch calculation
                calculate_pitch_button.config(state=tk.NORMAL)

# Step 7: Calculate pitch distances
def calculate_pitch():
    global pin_coordinates, pixel_to_mm_ratio

    if len(pin_coordinates) < 2:
        result_label.config(text="Error: At least two pins are required to calculate pitch.")
        return

    if pixel_to_mm_ratio is None:
        result_label.config(text="Error: Calibration not done. Please calibrate first.")
        return

    # Calculate pitch distances
    pitch_distances = []
    for i in range(len(pin_coordinates) - 1):
        x1, y1 = pin_coordinates[i]
        x2, y2 = pin_coordinates[i + 1]
        distance_pixels = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        distance_mm = distance_pixels / pixel_to_mm_ratio
        pitch_distances.append(distance_mm)

    # Display the results
    result_text = "Pitch distances (in mm):\n"
    for i, distance in enumerate(pitch_distances):
        result_text += f"Pin {i+1} to Pin {i+2}: {distance:.2f} mm\n"
    result_label.config(text=result_text)

# Step 8: Create the GUI
root = tk.Tk()
root.title("Pin Detection and Calibration")

# Create GUI elements
load_button = tk.Button(root, text="Load Image", command=load_image)
load_button.pack(pady=10)

pin_button = tk.Button(root, text="Place Pins", command=place_pins, state=tk.DISABLED)
pin_button.pack(pady=10)

submit_pins_button = tk.Button(root, text="Submit Pins", command=submit_pins, state=tk.DISABLED)
submit_pins_button.pack(pady=10)

calibrate_button = tk.Button(root, text="Calibrate", command=calibrate, state=tk.DISABLED)
calibrate_button.pack(pady=10)

calculate_pitch_button = tk.Button(root, text="Calculate Pitch", command=calculate_pitch, state=tk.DISABLED)
calculate_pitch_button.pack(pady=10)

result_label = tk.Label(root, text="Results will be displayed here.")
result_label.pack(pady=10)

# Create Matplotlib figure and canvas
fig, ax = plt.subplots(figsize=(8, 6))  # Larger figure size
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # Make the canvas resizable

# Add Matplotlib navigation toolbar for zooming and panning
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Run the GUI
root.mainloop()