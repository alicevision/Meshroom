# MrIMU - IMU Integration Plugin for Meshroom

MrIMU is a Meshroom plugin that integrates IMU (Inertial Measurement Unit) data from accelerometers and gyroscopes into photogrammetry workflows. This plugin helps improve camera pose estimation by constraining orientations using IMU measurements, particularly useful for maintaining vertical axis stability.

## Features

- **Load IMU Data**: Support for OpenCamera-Sensors CSV files and CAMM metadata from GoPro MP4 files
- **Gravity Vector Extraction**: Uses low-pass Butterworth filter to extract gravity direction from accelerometer data
- **Camera Pose Correction**: Applies IMU orientation constraints to StructureFromMotion camera poses
- **Adjustable IMU Influence**: Balance between optical and IMU data with configurable weight (0.0 to 1.0)
- **Z-Axis Locking**: Option to keep vertical axis aligned with gravity for stable reconstructions

## Plugin Structure

The MrIMU plugin follows Meshroom's plugin structure requirements:

```
MrIMU/
├── meshroom/                    # Meshroom nodes and pipelines
│   ├── __init__.py              # Plugin module initialization
│   ├── config.json              # Optional plugin configuration
│   └── nodes/                   # Node definitions
│       ├── __init__.py          # Required to be a Python module
│       ├── LoadIMUData.py       # Load IMU data node
│       ├── ApplyIMUConstraints.py # Apply IMU constraints node
│       └── imu_utils.py          # IMU processing utilities
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### Prerequisites

- Meshroom installed and configured
- Python packages: `numpy`, `scipy`

### Installation Steps

1. **Clone or download this plugin** to a directory of your choice:
   ```bash
   cd /path/to/plugins
   git clone <repository-url> MrIMU
   # or download and extract the plugin
   ```

2. **Set the MESHROOM_PLUGINS_PATH environment variable**:
   
   On Linux:
   ```bash
   export MESHROOM_PLUGINS_PATH=/path/to/plugins/MrIMU:$MESHROOM_PLUGINS_PATH
   ```
   
   On Windows:
   ```cmd
   set MESHROOM_PLUGINS_PATH=C:\path\to\plugins\MrIMU;%MESHROOM_PLUGINS_PATH%
   ```

3. **Install Python dependencies**:
   
   Option A: Install globally (if not already installed):
   ```bash
   pip install numpy scipy
   ```
   
   Option B: Create a virtual environment in the plugin directory:
   ```bash
   cd MrIMU
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Meshroom will automatically use the `venv/` directory if it exists.

4. **Restart Meshroom** to load the plugin

5. **Verify installation**: The plugin nodes should appear in the node library under the "IMU" category:
   - `LoadIMUData`
   - `ApplyIMUConstraints`

## Usage

### Workflow Overview

1. **Load IMU Data**: Use `LoadIMUData` node to process IMU CSV files or extract CAMM from MP4
2. **Run StructureFromMotion**: Execute Meshroom's standard SfM pipeline
3. **Apply IMU Constraints**: Use `ApplyIMUConstraints` node to correct camera poses with IMU data

### Node: LoadIMUData

Loads and processes IMU data from CSV files or MP4 videos.

#### Input Parameters

- **Video File** (optional): MP4 video file for CAMM extraction (GoPro format)
- **IMU Base Path**: Base path for OpenCamera-Sensors CSV files (without extension)
  - Expected files: `{basename}_accel.csv`, `{basename}_gyro.csv`, `{basename}_timestamps.csv`
  - Each CSV should have columns: `X`, `Y`, `Z`, `timestamp_ns`
- **IMU Format**: Choose between `opencamera` (CSV) or `camm` (MP4)
- **Gravity Filter Cutoff (Hz)**: Cutoff frequency for low-pass Butterworth filter (default: 0.1 Hz)
- **IMU Sampling Rate (Hz)**: Sampling rate of IMU data (default: 100.0 Hz)

#### Output Files

- **IMU Data**: Processed IMU data in JSON format
- **Gravity Vector**: Extracted gravity vector in NPY format (normalized, in world frame)

#### Example: OpenCamera-Sensors CSV Format

If your base path is `/data/my_session`, the plugin expects:
- `/data/my_session_accel.csv`
- `/data/my_session_gyro.csv`
- `/data/my_session_timestamps.csv`

Each CSV file should have the following structure:
```csv
X,Y,Z,timestamp_ns
0.123,0.456,9.789,1234567890000000000
0.124,0.457,9.790,1234567890100000000
...
```

### Node: ApplyIMUConstraints

Applies IMU orientation constraints to StructureFromMotion camera poses.

#### Input Parameters

- **SfM Scene**: Input SfM scene file from StructureFromMotion node
- **IMU Data**: Processed IMU data JSON file from LoadIMUData node
- **IMU Weight**: Weight for IMU data influence (0.0 = optical only, 1.0 = IMU only, default: 0.5)
- **Lock Z-Axis to Gravity**: Constrain vertical axis to align with gravity direction (default: True)

#### Output Files

- **Output Scene**: Corrected SfM scene file with IMU-adjusted camera poses

#### Usage Tips

- **Low IMU Weight (0.0-0.3)**: Use when optical data is reliable, IMU provides gentle guidance
- **Medium IMU Weight (0.4-0.6)**: Balanced approach, good for most scenarios
- **High IMU Weight (0.7-1.0)**: Use when optical tracking is poor but IMU data is reliable
- **Lock Z-Axis**: Enable for scenes where vertical stability is critical (architecture, indoor scans)

## Coordinate Systems

The plugin handles coordinate transformations between:

- **Android Sensor Frame** (OpenCamera-Sensors):
  - X: points east
  - Y: points north
  - Z: points up

- **World Frame** (Meshroom/AliceVision):
  - X: points right
  - Y: points down
  - Z: points forward

Transformations are automatically applied when processing IMU data.

## Technical Details

### Gravity Vector Extraction

The gravity vector is extracted using a 4th-order Butterworth low-pass filter applied to accelerometer data. This filters out high-frequency motion while preserving the constant gravity component.

### IMU Constraint Application

Camera poses are corrected by:
1. Extracting IMU-derived orientation from gravity and gyroscope data
2. Blending IMU orientation with optical SfM orientation based on IMU weight
3. Optionally locking Z-axis to gravity direction for vertical stability
4. Orthonormalizing the resulting rotation matrix

## Troubleshooting

### Common Issues

1. **"Missing IMU CSV files" error**
   - Verify file names match expected pattern: `{basename}_accel.csv`, etc.
   - Check that CSV files contain required columns: `X`, `Y`, `Z`, `timestamp_ns`

2. **"Could not extract CAMM data" error**
   - CAMM extraction from MP4 files requires proper MP4 box parsing
   - Currently, full CAMM extraction is not implemented
   - Use OpenCamera-Sensors CSV format instead

3. **"No valid IMU data found" error**
   - Check that CSV files are not empty
   - Verify data format matches expected structure
   - Ensure timestamps are in nanoseconds

4. **Plugin not appearing in Meshroom**
   - Verify `MESHROOM_PLUGINS_PATH` is set correctly
   - Check that plugin directory contains `meshroom/` subdirectory
   - Restart Meshroom after setting environment variable
   - Check Meshroom logs for plugin loading errors

## Limitations

- CAMM extraction from MP4 files is not fully implemented (placeholder)
- SfM scene format compatibility may vary with Meshroom versions
- IMU data must be synchronized with image capture timestamps (manual synchronization may be required)

## Contributing

Contributions are welcome! Please ensure:
- Code follows Meshroom plugin conventions
- Error handling and logging are included
- Documentation is updated

## License

This plugin follows the same license as Meshroom (MPL-2.0).

## References

- [Meshroom Plugin Documentation](https://github.com/alicevision/meshroom/wiki/Plugins)
- [OpenCamera-Sensors](https://github.com/almalence/OpenCamera-Sensors)
- [CAMM Metadata Specification](https://github.com/gopro/gpmf-parser)

