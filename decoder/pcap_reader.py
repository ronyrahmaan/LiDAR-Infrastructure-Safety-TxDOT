# decoder/pcap_reader.py

from scapy.all import rdpcap, UDP

def read_pcap(file_path):
    """
    Loads a pcap file and returns a list of raw UDP payloads (bytes)
    matching Velodyne packet size (1206 bytes).
    """
    packets = rdpcap(file_path)
    return [
        bytes(p[UDP].payload)
        for p in packets
        if UDP in p and len(p[UDP].payload) == 1206
    ]
