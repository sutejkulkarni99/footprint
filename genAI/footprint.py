import cv2
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
from scipy.spatial import distance as dist
import imutils  # Correct import
import os

def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) / 2, (ptA[1] + ptB[1]) / 2)

def process_image_and_create_pdf(image_path, ruler_known_length_mm, output_pdf_path):
    """Processes image, measures objects, creates PDF report."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found at: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts) # Use imutils.grab_contours

        if not cnts:
            raise ValueError("No contours found in the image.")

        # Find the contour with the largest area (likely the ruler)
        c = max(cnts, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        ruler_pixels = w
        pixels_per_mm = ruler_pixels / ruler_known_length_mm

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Footprint Analysis Report", ln=1, align="C")

        for c in cnts:
            if cv2.contourArea(c) < 100 or c is max(cnts, key=cv2.contourArea):
                continue

            orig = image.copy()
            box = cv2.minAreaRect(c)
            box = cv2.boxPoints(box)
            box = np.array(box, dtype="int")

            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
            for (x, y) in box:
                cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

            (tl, tr, br, bl) = box
            (tltrX, tltrY) = midpoint(tl, tr)
            (blbrX, blbrY) = midpoint(bl, br)
            (tlblX, tlblY) = midpoint(tl, bl)
            (trbrX, trbrY) = midpoint(tr, br)

            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

            dimA = dA / pixels_per_mm
            dimB = dB / pixels_per_mm

            fig, ax = plt.subplots()
            ax.plot([tl[0], tr[0], br[0], bl[0], tl[0]], [tl[1], tr[1], br[1], bl[1], tl[1]], 'b-')
            ax.set_aspect('equal')
            ax.set_title("CAD Representation")
            cad_image_path = "temp_cad.png"
            plt.savefig(cad_image_path)
            plt.close(fig)

            pdf.image(cad_image_path, w=100)
            os.remove(cad_image_path)

            pdf.cell(200, 10, txt=f"Object Dimensions: {dimA:.2f}mm x {dimB:.2f}mm", ln=1)

        pdf.output(output_pdf_path, "F")
        print(f"PDF report saved to {output_pdf_path}")

    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"Error processing image: {e}")

# Example usage:
image_path = "unnamed.jpg"
ruler_known_length_mm = 100
output_pdf_path = "footprint_report.pdf"

process_image_and_create_pdf(image_path, ruler_known_length_mm, output_pdf_path)