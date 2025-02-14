import cv2
import numpy as np
import svgwrite
from fpdf import FPDF

# Function to detect ruler and calculate scale
def detect_ruler_and_scale(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=50, maxLineGap=10)

    if lines is not None and len(lines) >= 2:
        first_mark = lines[0][0][0]
        second_mark = lines[1][0][0]
        pixels_per_mm = abs(second_mark - first_mark)
        return pixels_per_mm
    else:
        raise ValueError("Ruler not detected or not enough lines found.")

# Function to detect pins using advanced image processing
def detect_pins(image, pixels_per_mm):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Apply morphological operations to clean up the image
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    eroded = cv2.erode(dilated, kernel, iterations=1)

    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pins = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Filter out small contours (noise)
        if w > 20 and h > 20:  # Adjust thresholds as needed
            width_mm = w / pixels_per_mm
            height_mm = h / pixels_per_mm
            pins.append((x, y, width_mm, height_mm))

    # Sort pins by x-coordinate
    pins.sort(key=lambda pin: pin[0])

    # Calculate spacing between pins (pitch)
    pin_spacings = []
    for i in range(1, len(pins)):
        spacing_mm = (pins[i][0] - pins[i-1][0]) / pixels_per_mm
        pin_spacings.append((i, i+1, spacing_mm))  # Store pitch as (pin1, pin2, spacing)

    return pins, pin_spacings

# Function to create a PDF with text and visuals
def create_pdf_with_text_and_visuals(pins, pin_spacings, output_pdf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)  # Use core font to avoid deprecation warning

    # Add pin dimensions
    y_offset = 10
    for i, (x, y, width_mm, height_mm) in enumerate(pins):
        pdf.text(10, y_offset, f"Pin {i+1}: {width_mm:.2f}mm x {height_mm:.2f}mm")
        y_offset += 10  # Increase Y-coordinate for next line

    # Add pin spacings
    y_offset += 10  # Add extra space before pitch values
    for i, (pin1, pin2, spacing_mm) in enumerate(pin_spacings):
        pdf.text(10, y_offset, f"Pitch {pin1}-{pin2}: {spacing_mm:.2f}mm")
        y_offset += 10  # Increase Y-coordinate for next line

    # Add visual representation (rectangles for pins)
    y_offset += 10  # Add extra space before visuals
    for i, (x, y, width_mm, height_mm) in enumerate(pins):
        pdf.rect(50, y_offset, width_mm * 10, height_mm * 10)  # Scale for visibility
        y_offset += 20  # Increase Y-coordinate for next rectangle

    pdf.output(output_pdf)
    print(f"PDF file saved to {output_pdf}")

# Main function
def main():
    image_paths = [
        r'C:\Users\S\Desktop\genAI\image1.jpeg',
        r'C:\Users\S\Desktop\genAI\image2.jpeg',
        r'C:\Users\S\Desktop\genAI\image3.jpeg'
    ]

    all_pins = []
    all_spacings = []

    for image_path in image_paths:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Image not found: {image_path}")
            continue

        try:
            # Detect ruler and calculate scale
            pixels_per_mm = detect_ruler_and_scale(image)

            # Detect pins using advanced image processing
            pins, pin_spacings = detect_pins(image, pixels_per_mm)
            all_pins.extend(pins)
            all_spacings.extend(pin_spacings)

            print(f"Processed {image_path}: Found {len(pins)} pins and {len(pin_spacings)} spacings")
        except ValueError as e:
            print(f"Error processing {image_path}: {e}")

    if all_pins:
        # Create PDF with text and visuals
        pdf_path = r'C:\Users\S\Desktop\genAI\connector_drawing.pdf'
        create_pdf_with_text_and_visuals(all_pins, all_spacings, pdf_path)
    else:
        print("No valid pins found.")

if __name__ == "__main__":
    main()