# LiDAR-Infrastructure-Safety-TxDOT

A real-time LiDAR data processing pipeline designed for proactive traffic safety analysis and infrastructure intelligence. Developed as part of the Texas Department of Transportation (TxDOT) research initiative, this project captures, segments, and decodes Velodyne VLP-32C LiDAR data with precise timestamp alignment for frame-level interpretation.

---

## 🚦 Project Overview

This system enables:

- Real-time recording of LiDAR packets via UDP
- Automated segmentation into 0.3s PCAP chunks
- Further splitting into 0.1s frames (33 segments → 99 frames per 10s)
- Frame-wise CSV generation (x, y, z, intensity, timestamp)
- Visualization-ready outputs for tools like VeloView and ParaView
- Modular decoding calibrated for Velodyne VLP-32C

---

## 🧭 Folder Structure

```
LiDAR-Infrastructure-Safety-TxDOT/
│
├── live_reader.py              # Main real-time pipeline
├── decoder/                    # Packet decoding and calibration modules
│   ├── packet_data.py
│   ├── data_block.py
│   └── calibration.py
|       .......
├── out_csv/                    # Output CSVs and PCAP segments
│   ├── segments/               # 0.3s PCAPs
│   ├── pcap_slices/            # 0.1s PCAPs
│   └── csv_frames/             # Final decoded CSVs (per frame)
├── requirements.txt            # Dependencies
├── extract_azimuth_from_pcap.py  # Optional tool
└── README.md
```

---

## ⚙️ How to Run

1. **Set up the environment**

```bash
pip install -r requirements.txt
```

2. **Run the live reader**

```bash
python live_reader.py
```

This will:

- Capture 10s of LiDAR data
- Split into 33 × 0.3s segments
- Split each 0.3s into 3 × 0.1s PCAPs
- Generate 1 CSV per 0.1s frame (total 99 per 10s)

---

## 📁 Notes

- **PCAP files are excluded** due to size limits. To test the system, place your `.pcap` files in the appropriate subfolders.
- Supports only **Velodyne VLP-32C** (hardcoded configuration).
- All outputs are timestamp-aligned and compatible with visualization tools.

---

## 🧪 Tested With

- **Sensor**: Velodyne VLP-32C
- **OS**: macOS (M4 Pro)
- **RAM**: 24 GB
- **Tools**: VeloView, ParaView, Wireshark

---

## 📌 License

This project is part of a sponsored research effort. Please contact the author for licensing or collaboration inquiries.

---

## 👤 Author

Md A Rahman  
Graduate Researcher, Texas Tech University  
Lead Engineer, TxDOT Infrastructure Safety Project  
📧 [Contact](mailto:ara02434@ttu.edu)

