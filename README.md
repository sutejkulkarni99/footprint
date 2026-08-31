# KiCad Footprint Automation

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.4%2B-green.svg)](https://doc.qt.io/qtforpython/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Automated PCB footprint generation from connector and PCB images using OpenCV, edge detection, and homography correction.**

---

## 📖 Overview

This tool automates the tedious process of creating PCB footprints for KiCad. Instead of manually measuring pin positions and creating footprints by hand, you can:

1. Take a photo of a connector or PCB.
2. Load the image into the tool.
3. Select a reference square (for perspective correction).
4. Place pins on the image.
5. Calibrate using a ruler in the image.
6. Export to:
   - **KiCad footprint (.kicad_mod)** – IPC-7351 compliant
   - **2D CAD drawing** (SVG or PNG)
   - **3D STEP file** (for mechanical integration)

---

## ✨ Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Image Loading** | Supports JPG, JPEG, PNG, and BMP formats. |
| **Perspective Correction** | Select a known square in the image to correct for angle and distortion. |
| **Edge Detection** | Uses Canny edge detection to highlight pin boundaries. |
| **Snap-to-Edge** | Smart snapping to detected edges for precise pin placement. |
| **Multi‑Row Pins** | Supports multiple rows of pins (e.g., dual‑row headers). |
| **Ruler Calibration** | Click two points on a ruler in the image and enter the known distance to calibrate pixel‑to‑mm conversion. |
| **Pin Pitch Approximation** | Automatically suggests standard pitch sizes (2.54 mm, 1.27 mm, etc.). |
| **Polygon Border Selection** | Draw a polygon to define the PCB outline. |

### Export Options

| Export Type | Format | Description |
|-------------|--------|-------------|
| KiCad Footprint | `.kicad_mod` | IPC‑7351 compliant, ready to use in KiCad. |
| 2D Drawing | SVG / PNG | Vector or raster drawing with dimensions and annotations. |
| 3D Model | STEP (.step) | 3D model for mechanical integration. |

### User Interface

- **Intuitive GUI** built with PySide6.
- **Draggable pins** with snap‑to‑edge.
- **Live preview** of pin placement.
- **Industrial‑style controls** for calibration and export.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10** or later
- **pip** (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sutejkulkarni99/kicad-footprint-automation.git
   cd kicad-footprint-automation

    Install dependencies:
    bash

    pip install -r requirements.txt

    Run the tool:
    bash

    python working/footprint_gui33working.py

Example Workflow

    Load an image of a connector or PCB.

    Select a square in the image (e.g., a known 10 mm × 10 mm square on the board).

    Place pins by clicking on the image (left‑click to place, right‑click to remove).

    Calibrate by clicking two points on a ruler in the image and entering the known distance.

    Export the footprint as a KiCad .kicad_mod file, 2D SVG, or 3D STEP.

📁 Repository Structure
text

kicad-footprint-automation/
├── working/                 # Latest working GUI versions (v17–v33)
│   └── footprint_gui33working.py   ← 🔥 LATEST & BEST
│
├── tools/                   # Core footprint‑related utilities
│   ├── footprint.py         # Basic footprint generator
│   ├── footprint_2.0.py     # Enhanced version
│   ├── footprint-3.0.py     # CAD integration
│   ├── footprint-4.0.py     # Advanced features
│   ├── footprint_8.0.py     # Pin detection
│   ├── pin_detect_gem.py    # Pin detection with Gemini
│   ├── perspective cor.py   # Perspective correction helper
│   ├── xl_csv.py            # Excel/CSV conversion
│   ├── file conv v2/v3.py   # File conversion tools
│   ├── AI_file_conv.py      # AI‑assisted file conversion
│   ├── gemini excel.py      # Gemini Excel integration
│   └── py footprint gen.py  # Python footprint generation
│
├── misc/                    # Miscellaneous unrelated scripts
│   ├── batgui.py            # Battery monitoring
│   ├── print*.py            # Print utilities
│   ├── stopwatch.py         # Stopwatch
│   ├── genAI*.py            # Generic AI experiments
│   └── model_Training*.py   # ML model training
│
├── archive/                 # Old versions (v1–v16, gem, gpt, untitled)
│   └── footprint_gui*.py    # Historical development versions
│
├── data/                    # Test data and outputs
│   ├── images/              # Sample images (JPG, JPEG, PNG)
│   ├── excel/               # Excel data (XLSX, TSV, XML)
│   ├── cad/                 # CAD files (STEP, STP, DXF, KiCad mod)
│   ├── models/              # ML models (YOLO)
│   └── outputs/             # Generated outputs (PDF, SVG)
│
├── README.md                # This file
├── LICENSE                  # MIT License
└── requirements.txt         # Python dependencies

🛠️ Dependencies

Create a requirements.txt file if it doesn't exist:
bash

cat > requirements.txt << 'REQ'
PySide6>=6.4.0
opencv-python>=4.8.0
numpy>=1.24.0
matplotlib>=3.7.0
scipy>=1.10.0
cadquery>=2.4.0
reportlab>=4.0.0
Pillow>=10.0.0
ezdxf>=1.0.0
qrcode>=7.4.0
REQ

Install dependencies:
bash

pip install -r requirements.txt

📖 User Guide
1. Loading an Image

    Click Load Image and select a JPG, JPEG, or PNG file.

    The image will appear in the main viewport.

2. Selecting a Square (Perspective Correction)

    Click Select Square.

    Click on the four corners of a known square in the image.

    Click Submit Square Points to apply perspective correction.

3. Placing Pins

    Click Select Pins.

    Click on the image to place pins.

    Right‑click to remove the last pin.

    Click Submit Row to confirm the row.

    Use Add New Row to add additional rows.

4. Calibrating with a Ruler

    Click Calibrate Ruler.

    Click on two points on a ruler in the image.

    Enter the known distance between the two points (in mm).

    The tool will calculate the pixel‑to‑mm ratio.

5. Exporting
Export OptionDescription
Generate FootprintCreates a KiCad .kicad_mod file.
Generate 2D DrawingCreates an SVG or PNG drawing with dimensions.
Generate STEP FileCreates a 3D STEP model.
🔧 Troubleshooting
IssueSolution
No edges detectedAdjust the Canny threshold values in the code or ensure the image has good contrast.
Calibration failsMake sure the ruler is clearly visible and the two points are accurately placed.
Export failsEnsure you have write permissions in the output directory.
GUI crashesCheck that all dependencies are installed correctly.
🤝 Contributing

Contributions are welcome! If you'd like to improve the tool:

    Fork the repository.

    Create a new branch.

    Make your changes.

    Submit a pull request.

📜 License

This project is licensed under the MIT License — see the LICENSE file for details.
👤 Author

Sutej Kulkarni

    Email: sutejkulkarni99@gmail.com

    LinkedIn: sutej-kulkarni

    GitHub: sutejkulkarni99

⭐ Acknowledgments

    The development was inspired by the need to automate PCB footprint creation for KiCad.

    Special thanks to the open‑source community for providing the tools that made this possible.

📌 Keywords

PCB footprint generation, KiCad, OpenCV, Python GUI, PySide6, IPC-7351, PCB design automation, connector footprint, image processing, homography correction, edge detection

