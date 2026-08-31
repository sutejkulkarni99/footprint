import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance as dist
import imutils
import os
import ezdxf

def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) / 2, (ptA[1] + ptB[1]) / 2)

def detect_pins_hough(image_path):
    """Detects pins using Hough Circle Transform."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at: {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)  # Blur the image

    # Tune these parameters carefully!
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=30, minRadius=1, maxRadius=40)
    return image, circles

def create_cad_model_hough(image, circles, pixels_per_mm, output_cad_path):
    """Creates CAD model from Hough circles."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            msp.add_circle((x / pixels_per_mm, y / pixels_per_mm), r / pixels_per_mm)

    doc.saveas(output_cad_path)
    print(f"CAD model saved to {output_cad_path}")

def process_image_and_create_cad_hough(image_path, ruler_known_length_mm, output_cad_path):
    try:
        image, circles = detect_pins_hough(image_path)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if not cnts:
            raise ValueError("No contours found in the image. Check for ruler presence and clarity.")
        c = max(cnts, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(c)
        ruler_pixels = w
        pixels_per_mm = ruler_pixels / ruler_known_length_mm

        create_cad_model_hough(image, circles, pixels_per_mm, output_cad_path)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__": #This makes the code executable
    # Install dependencies (using subprocess for cross-platform compatibility)
    import subprocess
    try:
        import cv2
        import numpy as np
        import matplotlib.pyplot as plt
        import scipy
        import imutils
        import ezdxf
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call(['pip', 'install', 'opencv-python', 'numpy', 'matplotlib', 'scipy', 'imutils', 'ezdxf'])
        print("Packages installed. Please restart the script.")
        exit()

    # Example usage:
    image_path = "unnamed.jpg"  # Replace with your image path
    ruler_known_length_mm = 100  # Replace with the actual ruler length in mm
    output_cad_path = "pins_model_hough.dxf"

    process_image_and_create_cad_hough(image_path, ruler_known_length_mm, output_cad_path)