import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# Define paths
image_dir = "C:/Users/S/Desktop/genAI"
annotation_dir = "C:/Users/S/Desktop/connector dataset"
output_file = "connector_dataset/annotations/annotations.json"

# Initialize COCO format
coco_format = {
    "info": {
        "description": "Connector Dataset",
        "version": "1.0",
        "year": datetime.now().year,
        "contributor": "Your Name",
        "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    "licenses": [],
    "images": [],
    "annotations": [],
    "categories": [{"id": 1, "name": "pin", "supercategory": "none"}]
}

# Add images and annotations
image_id = 1
annotation_id = 1

for image_name in os.listdir(image_dir):
    if image_name.endswith(".jpg") or image_name.endswith(".png"):
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
        annotation_path = os.path.join(annotation_dir, image_name.replace(".jpg", ".xml"))
        if os.path.exists(annotation_path):
            tree = ET.parse(annotation_path)
            root = tree.getroot()

            for obj in root.findall("object"):
                # Get bounding box coordinates
                bbox = obj.find("bndbox")
                xmin = int(bbox.find("xmin").text)
                ymin = int(bbox.find("ymin").text)
                xmax = int(bbox.find("xmax").text)
                ymax = int(bbox.find("ymax").text)

                # Add annotation to COCO format
                coco_format["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": 1,  # "pin" category
                    "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],  # [x, y, width, height]
                    "area": (xmax - xmin) * (ymax - ymin),
                    "iscrowd": 0
                })
                annotation_id += 1

        image_id += 1

# Save COCO annotations to JSON file
with open(output_file, "w") as f:
    json.dump(coco_format, f, indent=4)

print(f"COCO annotations saved to {output_file}")