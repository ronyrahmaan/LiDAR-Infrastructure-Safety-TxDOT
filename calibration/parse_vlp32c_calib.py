
import os
import xml.etree.ElementTree as ET
import csv

# Paths (this script lives in calibration/)
CAL_DIR  = os.path.dirname(__file__)
XML_IN   = os.path.join(CAL_DIR, "VLP-32c.xml")
CSV_OUT  = os.path.join(CAL_DIR, "VLP-32C-Data-Order-in-Data-Block.csv")

def parse_vlp32c_xml(xml_path, csv_out):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    pts = root.find('.//points_')
    if pts is None:
        raise RuntimeError("No <points_> section found in XML")

    os.makedirs(os.path.dirname(csv_out), exist_ok=True)
    with open(csv_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Laser ID', 'Elevation Angle (°)', 'Azimuth Offset (δ)'])
        for item in pts.findall('item'):
            px   = item.find('px')
            lid  = int(float(px.find('id_').text))
            # These corrections are already in degrees:
            azi  = float(px.find('rotCorrection_').text)   # horizontal offset in ° 
            vert = float(px.find('vertCorrection_').text) # vertical offset in °
            writer.writerow([lid, f"{vert:.6f}", f"{azi:.6f}"])

    print(f"[OK] Wrote {csv_out}")

if __name__ == "__main__":
    parse_vlp32c_xml(XML_IN, CSV_OUT)
