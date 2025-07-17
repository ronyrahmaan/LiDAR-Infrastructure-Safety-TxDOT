# main.py

import os
import csv
import logging

from config import PCAP_DIR, OUTPUT_DIR, DISTANCE_RESOLUTION
from decoder.pcap_reader       import read_pcap
from decoder.packet_parser     import parse_packet_dual as parse_packet
from decoder.calibration       import (
    load_data_order_and_angles,
    load_firing_sequence,
    load_timing_offsets
)
from decoder.coordinate_transform import compute_cartesian
from decoder.timestamp_utils      import apply_timing_offset

ROTATION_RATE_DEG_PER_US = 360.0 / 100_000.0  # 360° per 100ms

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def main():
    setup_logging()
    log = logging.getLogger(__name__)

    # Load calibration
    laser_map, vertical_angles, azimuth_offsets = load_data_order_and_angles()
    firing_seq = load_firing_sequence()
    timing_offsets = load_timing_offsets()

    if firing_seq.shape != (32, 2):
        raise RuntimeError(f"firing_sequence.csv must be (32,2), got {firing_seq.shape}")
    if timing_offsets.shape != (32, 12):
        raise RuntimeError(f"timing_offsets must be (32,12), got {timing_offsets.shape}")

    seq_primary   = dict(zip(firing_seq['Laser ID'], firing_seq.index))
    seq_secondary = dict(zip(firing_seq['Laser ID 2'], firing_seq.index))

    log.info(f"Calibration loaded: {len(laser_map)} lasers")

    # File input
    pcap_file = os.path.join(PCAP_DIR, "2025-05-09-18-27-40_Velodyne-VLP-32C-Data.pcap")
    packets   = read_pcap(pcap_file)
    log.info(f"Read {len(packets)} packets from PCAP")

    # Init
    frame_id          = 0
    frame_points      = []
    last_block_az_raw = None

    for pkt in packets:
        blocks, base_ts = parse_packet(pkt)
        for block_idx, (azi_raw, channels, _) in enumerate(blocks):
            block_start_deg = azi_raw / 100.0

            # Detect new frame on raw azimuth rollover
            if last_block_az_raw is not None and azi_raw < last_block_az_raw:
                _save_frame_csv(frame_points, frame_id)
                log.info(f"Frame {frame_id} saved ({len(frame_points)} pts)")
                frame_id      += 1
                frame_points   = []
            last_block_az_raw = azi_raw

            for ch_idx, (dist_raw, intensity, ret_id) in enumerate(channels):
                if dist_raw == 0:
                    continue

                lid        = laser_map[ch_idx]
                vert_ang   = vertical_angles[lid]
                offset_deg = azimuth_offsets[lid]
                row_idx    = seq_primary[lid] if ret_id == 0 else seq_secondary[lid]
                ts_point   = apply_timing_offset(base_ts, row_idx, block_idx, timing_offsets)

                # Final azimuth (Velodyne logic: anchor per block, not frame)
                dt_us   = ts_point - base_ts
                az_base = (block_start_deg - offset_deg) % 360.0
                az_deg  = (az_base + dt_us * ROTATION_RATE_DEG_PER_US + offset_deg) % 360.0
                az_int  = int(round(az_deg * 100))

                dist_m = dist_raw * DISTANCE_RESOLUTION
                x, y, z = compute_cartesian(dist_m, az_deg, vert_ang)

                frame_points.append([
                    int(intensity), lid, az_int,
                    f"{dist_m:.6f}", ts_point, ts_point,
                    f"{vert_ang:.6f}", f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"
                ])

    if frame_points:
        _save_frame_csv(frame_points, frame_id)
        log.info(f"Final frame {frame_id} saved ({len(frame_points)} pts)")

def _save_frame_csv(points, frame_id):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"frame_{frame_id}.csv")
    header = [
        'intensity','laser_id','azimuth','distance_m',
        'adjustedtime','timestamp','vertical_angle',
        'Points_m_XYZ:0','Points_m_XYZ:1','Points_m_XYZ:2'
    ]
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(points)

if __name__ == '__main__':
    main()
