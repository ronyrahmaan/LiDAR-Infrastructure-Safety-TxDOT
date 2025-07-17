import os
import pandas as pd

# Base directory: where this script resides
BASE_DIR = os.path.dirname(__file__)

# Calibration file paths in the decoder folder
DATA_ORDER_PATH      = os.path.join(BASE_DIR, 'VLP-32C-Data-Order-in-Data-Block.csv')
FIRING_SEQUENCE_PATH = os.path.join(BASE_DIR, 'firing_sequence.csv')
TIMING_OFFSETS_PATH  = os.path.join(BASE_DIR, 'timing_offsets.csv')


def load_data_order_and_angles():
    """
    Reads the VLP-32C Data Order CSV and returns:
      - laser_id_map: Dict[channel_idx -> laser_id]
      - vertical_angles: Dict[channel_idx -> elevation angle (°)]
      - azimuth_offsets: Dict[channel_idx -> azimuth offset (°)]
    """
    df = pd.read_csv(DATA_ORDER_PATH)
    laser_id_map    = {idx: int(row['Laser ID']) for idx, row in df.iterrows()}
    vertical_angles = {idx: float(row['Elevation Angle (°)']) for idx, row in df.iterrows()}
    azimuth_offsets = {idx: float(row['Azimuth Offset (δ)']) for idx, row in df.iterrows()}
    return laser_id_map, vertical_angles, azimuth_offsets


def load_firing_sequence():
    """
    Reads the firing sequence CSV for per-firing ordering info.
    Returns a pandas.DataFrame.
    """
    return pd.read_csv(FIRING_SEQUENCE_PATH)


def load_timing_offsets():
    """
    Reads the timing offsets table: rows = firing sequence index (0–31),
    columns = block index (0–11). Returns a numpy array of shape (32, 12).
    """
    # Read raw CSV without indexing to preserve 32x12 layout
    df = pd.read_csv(TIMING_OFFSETS_PATH, header=None)
    # Ensure correct shape
    if df.shape != (32, 12):
        raise ValueError(f"Expected timing_offsets shape (32,12), got {df.shape}")
    return df.to_numpy()


if __name__ == '__main__':
    lid_map, vert_angles, azi_offsets = load_data_order_and_angles()
    print(f"Loaded {len(lid_map)} channels.")
    fs = load_firing_sequence()
    print(f"Firing seq rows: {len(fs)}")
    to = load_timing_offsets()
    print(f"Timing offsets shape: {to.shape}")
