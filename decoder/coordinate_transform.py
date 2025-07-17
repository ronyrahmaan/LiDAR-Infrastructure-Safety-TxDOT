# decoder/coordinate_transform.py

import math

def compute_cartesian(distance_m, azimuth_deg, vertical_angle_deg):
    """
    Convert polar LiDAR returns (distance, azimuth, vertical angle)
    into Cartesian coordinates (x, y, z).
    """
    azimuth_rad = math.radians(azimuth_deg)
    vertical_rad = math.radians(vertical_angle_deg)

    x = distance_m * math.cos(vertical_rad) * math.sin(azimuth_rad)
    y = distance_m * math.cos(vertical_rad) * math.cos(azimuth_rad)
    z = distance_m * math.sin(vertical_rad)

    return x, y, z
