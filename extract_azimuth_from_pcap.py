from scapy.all import rdpcap, UDP
import struct
import pandas as pd

# 1) Load the first Velodyne data packet (port 2368) from your PCAP
pkts = rdpcap("2025-05-09-18-27-40_Velodyne-VLP-32C-Data.pcap")
raw_payload = None
for p in pkts:
    if UDP in p and (p[UDP].sport == 2368 or p[UDP].dport == 2368):
        raw_payload = bytes(p[UDP].payload)
        break

if raw_payload is None:
    raise RuntimeError("No Velodyne packet on port 2368 found in PCAP")

# 2) Extract raw azimuth (bytes 2–3 of the UDP payload)
raw_azi = struct.unpack("<H", raw_payload[2:4])[0]

# 3) Load your decoded CSV and get its first azimuth
df = pd.read_csv("out_csv/frame_0.csv")
dec_azi = int(df.loc[0, "azimuth"])

# 4) Print both values
print(f"Raw:     {raw_azi} → {raw_azi/100:.2f}°")
print(f"Decoded: {dec_azi} → {dec_azi/100:.2f}°")
