import os
import xml.etree.ElementTree as ET
import json
from PIL import Image

# Define paths
image_dir = r"C:\Users\S\Desktop\connector dataset\images"
annotation_dir = r"C:\Users\S\Desktop\connector dataset\annot"
output_dir = r"C:\Users\S\Desktop\connector dataset"
output_file = os.path.join(output_dir, "coco_annotations.json")

# Path to classes.txt
classes_file = os.path.join(annotation_dir, "classes.txt")  # Updated path

# Check if classes.txt exists
if not os.path.exists(classes_file):
    raise FileNotFoundError(f"classes.txt not found at: {classes_file}")

# Initialize COCO format
coco_format = {
    "info": {
        "description": "Connector Dataset",
        "version": "1.0",
        "year": 2025,
        "contributor": "Your Name",
        "date_created": "2025-01-14 13:36:27"
    },
    "licenses": [],
    "images": [],
    "annotations": [],
    "categories": []
}

# Add categories
with open(classes_file, "r") as f:
    classes = [line.strip() for line in f.readlines()]

for i, class_name in enumerate(classes):
    coco_format["categories"].append({
        "id": i + 1,
        "name": class_name,
        "supercategory": "none"
    })

# Add images and annotations
image_id = 1
annotation_id = 1

for image_name in os.listdir(image_dir):
    if image_name.endswith(".jpg") or image_name.endswith(".jpeg"):
        # Add image to COCO format
        image_path = os.path.join(image_dir, image_name)
        image_width, image_height = Image.open(image_path).size
        coco_format["images"].append({
            "id": image_id,
            "file_name": image_name,
            "width": image_width,
            "height": image_height
        })

        # Parse PascalVOC annotation
        annotation_path = os.path.join(annotation_dir, image_name.replace(".jpg", ".xml").replace(".jpeg", ".xml"))
        if os.path.exists(annotation_path):
            tree = ET.parse(annotation_path)
            root = tree.getroot()

            for obj in root.findall("object"):
                # Get class name and category ID
                class_name = obj.find("name").text
                category_id = classes.index(class_name) + 1

                # Get bounding box coordinates
                bbox = obj.find("bndbox")
                xmin = int(bbox.find("xmin").text)
                ymin = int(bbox.find("ymin").text)
                xmax = int(bbox.find("xmax").text)
                ymax = int(bbox.find("ymax").text)

                # Convert to COCO format [x, y, width, height]
                width = xmax - xmin
                height = ymax - ymin

                # Add annotation to COCO format
                coco_format["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_id,
                    "bbox": [xmin, ymin, width, height],
                    "area": width * height,
                    "iscrowd": 0
                })
                annotation_id += 1

        image_id += 1

# Save COCO annotations to JSON file
with open(output_file, "w") as f:
    json.dump(coco_format, f, indent=4)

print(f"COCO annotations saved to {output_file}")