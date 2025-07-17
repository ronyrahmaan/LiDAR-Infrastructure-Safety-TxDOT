import os
import argparse
import logging
import threading
import time
import csv
import platform
import subprocess
from queue import Queue, Empty

from scapy.all import sniff, PcapWriter, get_if_list, rdpcap, UDP

from config import OUTPUT_DIR, DISTANCE_RESOLUTION
from decoder.packet_parser     import parse_packet_dual as parse_packet
from decoder.calibration       import (
    load_data_order_and_angles,
    load_firing_sequence,
    load_timing_offsets
)
from decoder.coordinate_transform import compute_cartesian
from decoder.timestamp_utils      import apply_timing_offset

# One revolution = 360° per 100 ms → degrees per microsecond
ROTATION_RATE_DEG_PER_US = 360.0 / 100_000.0
FRAME_DURATION_SECONDS   = 0.1  # LiDAR frame period

def setup_main_logger(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "log.txt")
    fmt = logging.Formatter("%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(ch)
    logging.info(f"Logging initialized at: {log_file}")

def auto_detect_interface(timeout: float = 2.0, filter_expr: str = "udp port 2368") -> str:
    """
    Safe interface auto-detection.
    macOS: uses `ifconfig` to find status: active interfaces.
    Skips virtual, loopback, and unsupported interfaces.
    """
    skip_keywords = ['lo', 'loopback', 'gif', 'stf', 'anpi', 'utun', 'awdl',
                     'vmnet', 'p2p', 'tap', 'bridge', 'llw', 'ap', 'vm']
    system = platform.system().lower()

    def get_active_mac_interfaces():
        try:
            output = subprocess.check_output(["ifconfig"]).decode()
            active = []
            current = None
            for line in output.splitlines():
                if line and not line.startswith('\t') and not line.startswith(' '):
                    current = line.split(":")[0]
                elif 'status: active' in line and current:
                    active.append(current)
            return [i for i in active if not any(k in i.lower() for k in skip_keywords)]
        except Exception as e:
            logging.warning(f"[AutoDetect] Failed to parse ifconfig: {e}")
            return []

    if system == "darwin":
        candidates = get_active_mac_interfaces()
    else:
        candidates = [i for i in get_if_list() if not any(k in i.lower() for k in skip_keywords)]

    logging.info(f"[AutoDetect] OS={system}, Candidates={candidates}")

    for iface in candidates:
        try:
            logging.info(f"Probing interface {iface}…")
            samples = sniff(iface=iface, timeout=timeout, filter=filter_expr, count=1, store=True)
            if samples:
                logging.info(f"Detected Velodyne traffic on {iface}")
                return iface
        except Exception as e:
            logging.warning(f"Skipping interface {iface} → {e}")
            continue

    if candidates:
        logging.warning(f"No traffic seen; defaulting to {candidates[0]}")
        return candidates[0]

    raise RuntimeError("No usable interface found")

def split_and_convert_segment(seg_path: str, label: str, output_dir: str, seg_len: float):
    try:
        pkts = rdpcap(seg_path)
    except Exception as e:
        logging.error(f"[ERROR] Cannot read {seg_path}: {e}")
        return

    total_pkts = len(pkts)
    if total_pkts == 0:
        logging.info(f"[SPLIT] {label}: 0 pkts (skipped)")
        return

    num_slices = max(1, int(round(seg_len / FRAME_DURATION_SECONDS)))
    base, extra = divmod(total_pkts, num_slices)
    idx = 0

    for slice_idx in range(1, num_slices + 1):
        count      = base + (1 if slice_idx <= extra else 0)
        slice_pkts = pkts[idx : idx + count]
        idx       += count

        slice_dir = os.path.join(output_dir, "pcap_slices", label)
        os.makedirs(slice_dir, exist_ok=True)
        slice_name = f"{label}_slice_{slice_idx}.pcap"
        slice_path = os.path.join(slice_dir, slice_name)
        writer = PcapWriter(slice_path, append=False, sync=True, linktype=1)
        for p in slice_pkts:
            writer.write(p)
        writer.close()
        logging.info(f"  [SPLIT]   {slice_name} -> {len(slice_pkts)} pkts")

        points = []
        for p in slice_pkts:
            if UDP not in p:
                continue
            raw = bytes(p[UDP].payload)
            blocks, base_ts = parse_packet(raw)
            for blk_idx, (azi_raw, channels, _) in enumerate(blocks):
                block_deg = azi_raw / 100.0
                for ch_idx, (dist_raw, intensity, ret_id) in enumerate(channels):
                    if dist_raw == 0:
                        continue
                    lid      = laser_map[ch_idx]
                    vert_ang = vertical_angles[lid]
                    az_off   = azimuth_offsets[lid]
                    row_idx  = seq_primary[lid] if ret_id == 0 else seq_secondary[lid]
                    ts_pt    = apply_timing_offset(base_ts, row_idx, blk_idx, timing_offsets)
                    dt_us    = ts_pt - base_ts
                    az_base  = (block_deg - az_off) % 360.0
                    az_deg   = (az_base + dt_us * ROTATION_RATE_DEG_PER_US + az_off) % 360.0
                    az_int   = int(round(az_deg * 100))
                    dist_m   = dist_raw * DISTANCE_RESOLUTION
                    x, y, z  = compute_cartesian(dist_m, az_deg, vert_ang)

                    points.append([
                        int(intensity), lid, az_int,
                        f"{dist_m:.6f}", ts_pt, ts_pt,
                        f"{vert_ang:.6f}", f"{x:.6f}", f"{y:.6f}", f"{z:.6f}"
                    ])

        csv_dir = os.path.join(output_dir, "csv_frames")
        os.makedirs(csv_dir, exist_ok=True)
        csv_name = f"{label}_frame_{slice_idx}.csv"
        csv_path = os.path.join(csv_dir, csv_name)
        if points:
            with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
                w = csv.writer(cf)
                w.writerow([
                    'intensity','laser_id','azimuth','distance_m',
                    'adjustedtime','timestamp','vertical_angle',
                    'Points_m_XYZ:0','Points_m_XYZ:1','Points_m_XYZ:2'
                ])
                w.writerows(points)
            logging.info(f"    [CSV]     {csv_name} created with {len(points)} pts")
        else:
            logging.info(f"    [CSV]     {csv_name} skipped (0 pts)")

def record_segments(iface: str, output_dir: str, segment_len: float, total_dur: float):
    pkt_q = Queue()
    threading.Thread(
        target=lambda: sniff(iface=iface,
                             filter="udp port 2368",
                             prn=pkt_q.put,
                             store=False),
        daemon=True
    ).start()
    logging.info("Packet capture thread started.")

    full_segments = int(total_dur // segment_len)

    for i in range(full_segments):
        start = time.time()
        label = f"{segment_len:.1f}s_seg{i+1}"
        fname = f"{label}.pcap"
        seg_dir = os.path.join(output_dir, "segments")
        os.makedirs(seg_dir, exist_ok=True)
        seg_path = os.path.join(seg_dir, fname)

        writer = PcapWriter(seg_path, append=False, sync=True, linktype=1)
        pkt_count = 0
        while time.time() < start + segment_len:
            try:
                p = pkt_q.get(timeout=0.01)
                writer.write(p)
                pkt_count += 1
            except Empty:
                continue
        writer.close()
        logging.info(f"[CAPTURE] Finished segment -> {fname} ({pkt_count} pkts)")

        threading.Thread(
            target=split_and_convert_segment,
            args=(seg_path, label, output_dir, segment_len),
            daemon=False
        ).start()

    logging.info("[CAPTURE] All segments captured. Conversions continue in background.")

def main():
    parser = argparse.ArgumentParser("LiDAR live → grouped CSV")
    parser.add_argument("-i", "--interface", help="capture interface")
    parser.add_argument("-o", "--output",    default=OUTPUT_DIR,
                        help="root output folder")
    parser.add_argument("-d", "--duration",  type=float, default=10.0,
                        help="total capture time (s)")
    parser.add_argument("-s", "--segment",   type=float, default=0.3,
                        help="per-segment length (s)")
    args = parser.parse_args()

    setup_main_logger(args.output)
    iface = args.interface or auto_detect_interface()
    logging.info(f"Using interface: {iface}")

    global laser_map, vertical_angles, azimuth_offsets
    global seq_primary, seq_secondary, timing_offsets

    laser_map, vertical_angles, azimuth_offsets = load_data_order_and_angles()
    fs = load_firing_sequence()
    timing_offsets = load_timing_offsets()
    seq_primary   = dict(zip(fs['Laser ID'],   fs.index))
    seq_secondary = dict(zip(fs['Laser ID 2'], fs.index))

    logging.info(f"Calibration loaded ({len(laser_map)} lasers)")
    record_segments(iface, args.output, args.segment, args.duration)

if __name__ == "__main__":
    main()
