# config.py

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CALIB_DIR = os.path.join(BASE_DIR, "calibration")
PCAP_DIR = os.path.join(BASE_DIR, "pcap_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "out_csv")
# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Calibration file paths
FIRING_SEQ_PATH     = os.path.join(CALIB_DIR, "firing_sequence.csv")
TIMING_OFFSETS_PATH = os.path.join(CALIB_DIR, "timing_offsets.csv")
DATA_ORDER_PATH     = os.path.join(CALIB_DIR, "VLP-32C-Data-Order-in-Data-Block.csv")

# Sensor and decoding configuration
DISTANCE_RESOLUTION  = 0.004  # meters per unit (4 mm) for VLP-32C
ROTATION_MAX_UNITS   = 36000   # hundredths of a degree for full 360°
PACKET_SIZE_STANDARD = 1206    # bytes for standard single-return packet
PACKET_SIZE_DUAL     = 554     # bytes for dual-return packets
BLOCKS_PER_PACKET    = 12      # blocks in each packet
CHANNELS_PER_BLOCK   = 32      # channels per block
FOOTER_SIZE          = 6       # bytes for GPS timestamp + factory field
