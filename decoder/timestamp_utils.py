# decoder/timestamp_utils.py

def apply_timing_offset(base_timestamp, row, col, timing_table):
    """
    Adjusts the raw packet timestamp by the per-firing offset.
    - base_timestamp: the packet’s timestamp (µs)
    - row: firing sequence row index (laser index)
    - col: block index within the packet
    - timing_table: 2D array of offsets (µs)
    Returns the corrected timestamp in integer microseconds.
    """
    try:
        offset_us = float(timing_table[row][col])
        return int(base_timestamp + offset_us)
    except:
        return int(base_timestamp)
