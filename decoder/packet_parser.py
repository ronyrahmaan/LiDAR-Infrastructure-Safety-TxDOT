# decoder/packet_parser.py

import struct

def parse_packet_dual(packet):
    """
    Parse all 12 data blocks in a Velodyne packet.
    Alternates returns by block index (even/odd).
    Returns:
      - blocks: List of tuples (azimuth, channels, block_idx)
        where channels is a list of (distance, intensity, return_id)
      - timestamp: Raw timestamp from the packet footer.
    """
    blocks = []
    for block_idx in range(12):
        offset = block_idx * 100
        block = packet[offset:offset+100]

        flag = struct.unpack("<H", block[0:2])[0]
        if flag != 0xEEFF:
            continue

        azimuth = struct.unpack("<H", block[2:4])[0]
        channels = []
        # 32 channels per block, each 3 bytes: 2 for distance, 1 for intensity
        for ch in range(32):
            i = 4 + ch * 3
            distance = struct.unpack("<H", block[i:i+2])[0]
            intensity = block[i+2]
            channels.append((distance, intensity, block_idx % 2))

        blocks.append((azimuth, channels, block_idx))

    # Timestamp in microseconds is stored in the last 4 bytes of the packet
    timestamp = struct.unpack("<I", packet[1200:1204])[0]
    return blocks, timestamp
