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

# Function to detect pins and measure their dimensions and spacing
def detect_pins(image, pixels_per_mm):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pins = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        width_mm = w / pixels_per_mm
        height_mm = h / pixels_per_mm
        pins.append((x, y, width_mm, height_mm))

    # Sort pins by x-coordinate
    pins.sort(key=lambda pin: pin[0])

    # Calculate spacing between pins
    pin_spacings = []
    for i in range(1, len(pins)):
        spacing_mm = (pins[i][0] - pins[i-1][0]) / pixels_per_mm
        pin_spacings.append(spacing_mm)

    return pins, pin_spacings

# Function to create a 2D CAD drawing in SVG format
def create_cad_drawing(pins, pin_spacings, output_svg):
    dwg = svgwrite.Drawing(output_svg, size=('210mm', '297mm'))  # A4 size

    # Draw pins
    for i, (x, y, width_mm, height_mm) in enumerate(pins):
        dwg.add(dwg.rect(insert=(10 + i * 20, 10), size=(width_mm, height_mm),
                         stroke='black', fill='none', stroke_width=0.5))
        dwg.add(dwg.text(f'Pin {i+1}: {width_mm:.2f}mm x {height_mm:.2f}mm',
                         insert=(10 + i * 20, 10 + height_mm + 5),
                         fill='black', font_size=5))

    # Draw pin spacings
    for i, spacing_mm in enumerate(pin_spacings):
        dwg.add(dwg.text(f'Spacing {i+1}-{i+2}: {spacing_mm:.2f}mm',
                         insert=(10 + i * 20, 50),
                         fill='black', font_size=5))

    dwg.save()
    print(f"SVG file saved to {output_svg}")

# Function to convert SVG to PDF
def svg_to_pdf(svg_path, pdf_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(svg_path, x=10, y=10, w=190)  # Fit SVG into A4 page
    pdf.output(pdf_path)
    print(f"PDF file saved to {pdf_path}")

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
            pixels_per_mm = detect_ruler_and_scale(image)
            pins, pin_spacings = detect_pins(image, pixels_per_mm)
            all_pins.extend(pins)
            all_spacings.extend(pin_spacings)
            print(f"Processed {image_path}: Found {len(pins)} pins and {len(pin_spacings)} spacings")
        except ValueError as e:
            print(f"Error processing {image_path}: {e}")

    if all_pins:
        # Create 2D CAD drawing in SVG format
        svg_path = r'C:\Users\S\Desktop\genAI\output.svg'
        create_cad_drawing(all_pins, all_spacings, svg_path)

        # Convert SVG to PDF
        pdf_path = r'C:\Users\S\Desktop\genAI\output.pdf'
        svg_to_pdf(svg_path, pdf_path)
    else:
        print("No valid pins found.")

if __name__ == "__main__":
    main()