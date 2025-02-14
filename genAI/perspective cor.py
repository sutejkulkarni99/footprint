import cv2
import numpy as np
from tkinter import Tk, filedialog
import matplotlib.pyplot as plt

# Step 1: Open a file dialog to select an image
def select_file():
    Tk().withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select an image file",
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff")]
    )
    return file_path

# Get the file path from the user
file_path = select_file()

if not file_path:
    print("No file selected. Exiting...")
    exit()

# Step 2: Load the selected image
image = cv2.imread(file_path)

if image is None:
    print("Error: Unable to load image. Please check the file path.")
    exit()

# Step 3: Convert the image to grayscale
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Step 4: Define the rotation matrix
angle = 45  # Rotation angle in degrees
height, width = gray_image.shape
center = (width // 2, height // 2)  # Rotation center
scale = 1.0  # Scaling factor

# Get the rotation matrix
rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)

# Step 5: Apply the rotation to the grayscale image
rotated_image = cv2.warpAffine(gray_image, rotation_matrix, (width, height))

# Step 6: Display the images using matplotlib
plt.figure(figsize=(10, 5))

# Original Image
plt.subplot(1, 3, 1)
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.title('Original Image')
plt.axis('off')

# Grayscale Image
plt.subplot(1, 3, 2)
plt.imshow(gray_image, cmap='gray', vmin=0, vmax=255)
plt.title('Grayscale Image')
plt.axis('off')

# Rotated Image
plt.subplot(1, 3, 3)
plt.imshow(rotated_image, cmap='gray', vmin=0, vmax=255)
plt.title('Rotated Image')
plt.axis('off')

plt.tight_layout()
plt.show()