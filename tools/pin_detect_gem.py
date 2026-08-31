import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

def process_image():
    filepath = filedialog.askopenfilename(title="Select Image", filetypes=(("Image files", "*.jpg;*.jpeg;*.png"), ("All files", "*.*")))
    if not filepath:
        return

    try:
        img = cv2.imread(filepath)
        if img is None:
            raise Exception("Could not open or read image")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. Contour-based method
        pin_centers_contour = detect_pins_contour(gray.copy())

        # 2. Hough Line Transform
        pin_centers_hough = detect_pins_hough(gray.copy())

        # Combine results and deduplicate
        all_centers = pin_centers_contour + pin_centers_hough
        unique_centers = []
        seen = set()
        for x, y in all_centers:
            if (x, y) not in seen:
                unique_centers.append((x, y))
                seen.add((x, y))

        # Calculate spacing
        spacing = "N/A"
        if len(unique_centers) >= 2:
            distances = []
            for i in range(len(unique_centers)):
                for j in range(i + 1, len(unique_centers)):
                    dist = np.sqrt((unique_centers[i][0] - unique_centers[j][0])**2 + (unique_centers[i][1] - unique_centers[j][1])**2)
                    distances.append(dist)
            if distances:
                distances = np.array(distances)
                median_dist = np.median(distances)
                filtered_distances = distances[np.abs(distances - median_dist) < 0.2 * median_dist]
                if len(filtered_distances) > 0:
                    spacing = np.mean(filtered_distances)
                else:
                    spacing = median_dist

        # Display results (Corrected to handle "N/A")
        if isinstance(spacing, (int, float)):
            result_text.set(f"Number of Pins: {len(unique_centers)}\nAverage Pin Spacing: {spacing:.2f} pixels")
        else:
            result_text.set(f"Number of Pins: {len(unique_centers)}\nAverage Pin Spacing: {spacing}")

        # Display image with detected pins (Resized to fit window)
        img_color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        for center in unique_centers:
            cv2.circle(img_color, center, 3, (0, 0, 255), -1)

        img_pil = Image.fromarray(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
        max_width = 500
        max_height = 500
        img_pil.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        image_label.config(image=img_tk)
        image_label.image = img_tk

    except Exception as e:
        result_text.set(f"Error: {e}")

def detect_pins_contour(gray):
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
    contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pin_centers = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 20 < area < 200:
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            if 0.5 < circularity < 1:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                if 0.8 < aspect_ratio < 1.2:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        pin_centers.append((cX, cY))
    return pin_centers

def detect_pins_hough(gray):
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    minLineLength = 20
    maxLineGap = 5
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength, maxLineGap)
    pin_centers = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            pin_centers.append(((x1 + x2) // 2, (y1 + y2) // 2))
    return pin_centers

# GUI setup
root = tk.Tk()
root.title("Pin Detector")
root.resizable(True, True)  # Make window resizable
root.minsize(300, 200)       # Set minimum size

browse_button = tk.Button(root, text="Browse", command=process_image)
browse_button.pack(pady=10)

result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text)
result_label.pack()

image_label = tk.Label(root)
image_label.pack()

root.mainloop()