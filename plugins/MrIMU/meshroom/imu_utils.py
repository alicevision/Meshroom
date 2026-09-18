"""
IMU data processing utilities for Meshroom photogrammetry integration.

This module provides functions for:
- Loading IMU data from OpenCamera-Sensors CSV files
- Extracting CAMM metadata from MP4 files (GoPro format)
- Processing IMU data with Butterworth filters
- Coordinate system transformations between Android sensor frame and world frame
"""

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
from scipy import signal


@dataclass
class IMUData:
    """Container for IMU sensor data."""

    timestamps: np.ndarray  # in nanoseconds
    accel: np.ndarray  # shape: (N, 3) - X, Y, Z accelerometer data
    gyro: np.ndarray  # shape: (N, 3) - X, Y, Z gyroscope data

    def __len__(self):
        return len(self.timestamps)


class IMUProcessor:
    """Processes IMU data for photogrammetry integration."""

    def __init__(self, imu_data: IMUData):
        """
        Initialize IMU processor with IMU data.

        Args:
            imu_data: IMUData object containing sensor measurements
        """
        self.imu_data = imu_data
        self._gravity_vector: Optional[np.ndarray] = None
        self._orientation: Optional[np.ndarray] = None

    def extract_gravity_vector(
        self, cutoff_freq: float = 0.1, sampling_rate: float = 100.0
    ) -> np.ndarray:
        """
        Extract gravity vector from accelerometer data using low-pass Butterworth filter.

        Args:
            cutoff_freq: Cutoff frequency for low-pass filter in Hz
                (default: 0.1)
            sampling_rate: Sampling rate of IMU data in Hz
                (default: 100.0)

        Returns:
            Gravity vector as numpy array [X, Y, Z] in sensor frame
        """
        if self._gravity_vector is not None:
            return self._gravity_vector

        accel_data = self.imu_data.accel

        # Design Butterworth low-pass filter
        nyquist = sampling_rate / 2.0
        normal_cutoff = cutoff_freq / nyquist
        b, a = signal.butter(4, normal_cutoff, btype="low", analog=False)

        # Apply filter to each axis
        filtered_accel = np.zeros_like(accel_data)
        for i in range(3):
            filtered_accel[:, i] = signal.filtfilt(b, a, accel_data[:, i])

        # Average the filtered data to get gravity vector
        gravity_vector = np.mean(filtered_accel, axis=0)

        # Normalize to unit vector
        gravity_norm = np.linalg.norm(gravity_vector)
        if gravity_norm > 0:
            gravity_vector = gravity_vector / gravity_norm

        self._gravity_vector = gravity_vector
        return gravity_vector

    def estimate_orientation(self) -> np.ndarray:
        """
        Estimate device orientation from IMU data.

        Returns:
            Rotation matrix (3x3) representing device orientation
        """
        if self._orientation is not None:
            return self._orientation

        # Extract gravity vector
        gravity = self.extract_gravity_vector()

        # In Android sensor frame:
        # - X points east
        # - Y points north
        # - Z points up

        # For world frame (Meshroom/AliceVision):
        # - X points right
        # - Y points down
        # - Z points forward

        # Transform gravity from Android sensor frame to world frame
        # Android: [X_east, Y_north, Z_up]
        # World: [X_right, Y_down, Z_forward]
        # Transformation: world = [Y_north, Z_up, -X_east]
        gravity_world = np.array([gravity[1], gravity[2], -gravity[0]])

        # Normalize
        gravity_norm = np.linalg.norm(gravity_world)
        if gravity_norm > 0:
            gravity_world = gravity_world / gravity_norm

        # Build rotation matrix to align Z-axis with gravity
        # We want Z-axis to point opposite to gravity (upward)
        z_axis = -gravity_world

        # Choose arbitrary X-axis perpendicular to Z
        if abs(z_axis[0]) < 0.9:
            x_axis = np.array([1, 0, 0])
        else:
            x_axis = np.array([0, 1, 0])

        # Gram-Schmidt orthogonalization
        x_axis = x_axis - np.dot(x_axis, z_axis) * z_axis
        x_axis = x_axis / np.linalg.norm(x_axis)

        # Y-axis is cross product of Z and X
        y_axis = np.cross(z_axis, x_axis)
        y_axis = y_axis / np.linalg.norm(y_axis)

        # Build rotation matrix
        rotation_matrix = np.column_stack([x_axis, y_axis, z_axis])

        self._orientation = rotation_matrix
        return rotation_matrix

    def constrain_z_axis_to_gravity(self) -> np.ndarray:
        """
        Constrain Z-axis to align with gravity direction.

        Returns:
            Rotation matrix (3x3) with Z-axis aligned to gravity
        """
        return self.estimate_orientation()


def load_opencamera_csv(base_path: str) -> IMUData:
    """
    Load IMU data from OpenCamera-Sensors CSV files.

    Expected files:
        - {basename}_accel.csv: accelerometer data with columns X, Y, Z, timestamp_ns
        - {basename}_gyro.csv: gyroscope data with columns X, Y, Z, timestamp_ns
        - {basename}_timestamps.csv: timestamps with column timestamp_ns

    Args:
        base_path: Base path without extension
            (e.g., "/path/to/data" for data_accel.csv)

    Returns:
        IMUData object containing loaded sensor data

    Raises:
        FileNotFoundError: If required CSV files are missing
        ValueError: If CSV files have invalid format
    """
    base_path_obj = Path(base_path)
    parent_dir = base_path_obj.parent
    basename = base_path_obj.name

    accel_file = parent_dir / f"{basename}_accel.csv"
    gyro_file = parent_dir / f"{basename}_gyro.csv"
    timestamps_file = parent_dir / f"{basename}_timestamps.csv"

    # Check if files exist
    missing_files = []
    if not accel_file.exists():
        missing_files.append(str(accel_file))
    if not gyro_file.exists():
        missing_files.append(str(gyro_file))
    if not timestamps_file.exists():
        missing_files.append(str(timestamps_file))

    if missing_files:
        raise FileNotFoundError(
            f"Missing IMU CSV files: {', '.join(missing_files)}"
        )

    def read_csv_data(filepath: Path) -> Tuple[np.ndarray, np.ndarray]:
        """Read CSV file and return data array and timestamps."""
        data = []
        timestamps = []

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Check required columns
            required_cols = ["X", "Y", "Z", "timestamp_ns"]
            if reader.fieldnames is None or not all(
                col in reader.fieldnames for col in required_cols
            ):
                raise ValueError(
                    f"CSV file {filepath} missing required columns. "
                    f"Found: {reader.fieldnames}, Required: {required_cols}"
                )

            for row in reader:
                try:
                    x = float(row["X"])
                    y = float(row["Y"])
                    z = float(row["Z"])
                    ts = int(row["timestamp_ns"])

                    data.append([x, y, z])
                    timestamps.append(ts)
                except (ValueError, KeyError) as e:
                    logging.warning(
                        "Skipping invalid row in %s: %s", filepath, e
                    )
                    continue

        return np.array(data), np.array(timestamps)

    # Load accelerometer data
    accel_data, accel_timestamps = read_csv_data(accel_file)

    # Load gyroscope data
    gyro_data, gyro_timestamps = read_csv_data(gyro_file)

    # Load timestamps (if separate file exists, use it;
    # otherwise use accel timestamps)
    # Validate timestamp synchronization between accel and gyro
    if not np.array_equal(accel_timestamps, gyro_timestamps):
        logging.warning(
            "Accelerometer and gyroscope timestamps differ. "
            "Using accelerometer timestamps."
        )

    if timestamps_file.exists():
        timestamps_list: list[int] = []
        with open(timestamps_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and "timestamp_ns" in reader.fieldnames:
                for row in reader:
                    try:
                        timestamps_list.append(int(row["timestamp_ns"]))
                    except (ValueError, KeyError):
                        continue
        if timestamps_list:
            timestamps: np.ndarray = np.array(timestamps_list)
        else:
            timestamps = accel_timestamps
    else:
        timestamps = accel_timestamps

    # Ensure all arrays have the same length (interpolate if needed)
    min_len = min(len(accel_data), len(gyro_data), len(timestamps))
    if min_len == 0:
        raise ValueError("No valid IMU data found in CSV files")

    accel_data = accel_data[:min_len]
    gyro_data = gyro_data[:min_len]
    timestamps = timestamps[:min_len]

    return IMUData(timestamps=timestamps, accel=accel_data, gyro=gyro_data)


def detect_camm_in_mp4(video_path: str) -> Optional[Dict[str, bool]]:
    """
    Extract CAMM (Camera Motion Metadata) from MP4 file (GoPro format).

    CAMM is stored in the 'camm' box/track of MP4 files.
    This function attempts to extract IMU data embedded in GoPro videos.

    Args:
        video_path: Path to MP4 video file

    Returns:
        Dictionary containing CAMM data if found, None otherwise

    Note:
        This is a simplified implementation. Full CAMM extraction requires
        proper MP4 box parsing. For production use, consider using libraries
        like 'mp4parse' or 'pyav'.
    """
    video_path_obj = Path(video_path)

    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if video_path_obj.suffix.lower() != ".mp4":
        logging.warning("File %s is not an MP4 file", video_path)
        return None

    # CAMM extraction requires parsing MP4 boxes
    # This is a placeholder implementation
    # In production, use a proper MP4 parser library

    try:
        with open(video_path_obj, "rb") as f:
            # Read file header to check for 'camm' box
            # This is simplified - full implementation needs proper MP4 box parsing
            data = f.read(1024)

            # Look for 'camm' box identifier
            if b"camm" in data:
                logging.info("Found CAMM metadata in %s", video_path)
                # TODO: Implement full CAMM box parsing
                # For now, return None to indicate CAMM was detected
                # but not extracted
                return {"detected": True, "extracted": False}
    except (IOError, OSError) as e:
        logging.error("Error reading MP4 file %s: %s", video_path, e)
        return None

    return None


def transform_android_to_world(android_vector: np.ndarray) -> np.ndarray:
    """
    Transform vector from Android sensor frame to world frame.

    Android sensor frame:
        - X: points east
        - Y: points north
        - Z: points up

    World frame (Meshroom/AliceVision):
        - X: points right
        - Y: points down
        - Z: points forward

    Args:
        android_vector: Vector in Android sensor frame [X, Y, Z]

    Returns:
        Vector in world frame [X, Y, Z]
    """
    # Transformation: world = [Y_north, Z_up, -X_east]
    return np.array([android_vector[1], android_vector[2], -android_vector[0]])


def save_imu_data_json(imu_data: IMUData, output_path: str) -> None:
    """
    Save IMU data to JSON file.

    Args:
        imu_data: IMUData object to save
        output_path: Path to output JSON file
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    data_dict = {
        "timestamps": imu_data.timestamps.tolist(),
        "accel": imu_data.accel.tolist(),
        "gyro": imu_data.gyro.tolist(),
    }

    with open(output_path_obj, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2)


def load_imu_data_json(input_path: str) -> IMUData:
    """
    Load IMU data from JSON file.

    Args:
        input_path: Path to input JSON file

    Returns:
        IMUData object
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data_dict = json.load(f)

    return IMUData(
        timestamps=np.array(data_dict["timestamps"]),
        accel=np.array(data_dict["accel"]),
        gyro=np.array(data_dict["gyro"]),
    )
