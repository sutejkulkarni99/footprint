def create_ipc7351_footprint(filename, footprint_name, num_pins, pitch, pin_diameter, tolerance=0.2, annular_ring=0.15):
    """
    Creates a KiCad footprint file (.kicad_mod) compliant with IPC-7351.

    Parameters:
    - filename: Output file name (e.g., "Connector_6pin.kicad_mod").
    - footprint_name: Name of the footprint (e.g., "Connector_6pin").
    - num_pins: Number of pins.
    - pitch: Distance between pins (in mm).
    - pin_diameter: Diameter of the pins (in mm).
    - tolerance: Drill tolerance (in mm).
    - annular_ring: Annular ring width (in mm).
    """
    drill_size = pin_diameter + tolerance
    pad_size = drill_size + 2 * annular_ring
    pad_size = max(pad_size, 1.5)  # Ensure minimum pad size

    content = f"(module {footprint_name} (layer F.Cu) (tedit 12345678)\n"
    content += "  (descr \"IPC-7351 compliant footprint\")\n"
    content += "  (tags \"connector\")\n"
    content += "  (attr through_hole)\n"
    content += f"  (fp_text reference J1 (at 0 -5.08) (layer F.SilkS)\n"
    content += "    (effects (font (size 1 1) (thickness 0.15))))\n"
    content += f"  (fp_text value {footprint_name} (at 0 5.08) (layer F.Fab)\n"
    content += "    (effects (font (size 1 1) (thickness 0.15))))\n"

    # Add silkscreen outline
    outline_width = (num_pins - 1) * pitch + pad_size
    outline_height = pad_size + 2.54
    content += f"  (fp_line (start {-outline_width/2} {-outline_height/2}) (end {outline_width/2} {-outline_height/2}) (layer F.SilkS) (width 0.15))\n"
    content += f"  (fp_line (start {outline_width/2} {-outline_height/2}) (end {outline_width/2} {outline_height/2}) (layer F.SilkS) (width 0.15))\n"
    content += f"  (fp_line (start {outline_width/2} {outline_height/2}) (end {-outline_width/2} {outline_height/2}) (layer F.SilkS) (width 0.15))\n"
    content += f"  (fp_line (start {-outline_width/2} {outline_height/2}) (end {-outline_width/2} {-outline_height/2}) (layer F.SilkS) (width 0.15))\n"

    # Add pin 1 marker
    content += f"  (fp_circle (center {-outline_width/2 + 1.27} 0) (end {-outline_width/2 + 2.54} 0) (layer F.SilkS) (width 0.15))\n"

    # Add pads
    for i in range(num_pins):
        x = i * pitch
        y = 0
        content += f"  (pad {i+1} thru_hole circle (at {x} {y}) (size {pad_size} {pad_size}) (drill {drill_size}) (layers *.Cu *.Mask F.SilkS))\n"

    # Add courtyard
    courtyard_clearance = 0.25
    courtyard_width = outline_width + 2 * courtyard_clearance
    courtyard_height = outline_height + 2 * courtyard_clearance
    content += f"  (fp_line (start {-courtyard_width/2} {-courtyard_height/2}) (end {courtyard_width/2} {-courtyard_height/2}) (layer F.CrtYd) (width 0.15))\n"
    content += f"  (fp_line (start {courtyard_width/2} {-courtyard_height/2}) (end {courtyard_width/2} {courtyard_height/2}) (layer F.CrtYd) (width 0.15))\n"
    content += f"  (fp_line (start {courtyard_width/2} {courtyard_height/2}) (end {-courtyard_width/2} {courtyard_height/2}) (layer F.CrtYd) (width 0.15))\n"
    content += f"  (fp_line (start {-courtyard_width/2} {courtyard_height/2}) (end {-courtyard_width/2} {-courtyard_height/2}) (layer F.CrtYd) (width 0.15))\n"

    content += ")\n"

    # Save to file
    with open(filename, "w") as f:
        f.write(content)
    print(f"Footprint saved as {filename}")

# Example usage
create_ipc7351_footprint(
    filename="sutej.kicad_mod",
    footprint_name="sutej",
    num_pins=6,
    pitch=2.54,
    pin_diameter=1.0
)