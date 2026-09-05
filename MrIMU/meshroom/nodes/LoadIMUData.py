__version__ = "1.0.0"

import os

import numpy as np

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

from .imu_utils import (
    IMUProcessor,
    detect_camm_in_mp4,
    load_opencamera_csv,
    save_imu_data_json,
    transform_android_to_world,
)


class LoadIMUData(desc.Node):
    """
    Load and process IMU (accelerometer and gyroscope) data from OpenCamera-Sensors CSV files
    or extract CAMM metadata from MP4 files (GoPro format).

    This node processes IMU data and extracts gravity vector using a low-pass Butterworth filter.
    The processed data can be used to constrain camera poses in photogrammetry workflows.
    """

    category = "IMU"
    documentation = """
Load and process IMU data for photogrammetry integration.

**Input Formats:**
- OpenCamera-Sensors CSV: Requires {basename}_accel.csv, {basename}_gyro.csv, and {basename}_timestamps.csv
- CAMM (GoPro): Extracts metadata from MP4 files

**Outputs:**
- Processed IMU data in JSON format
- Gravity vector in NPY format (normalized, in world frame)
"""

    inputs = [
        desc.File(
            name="videoFile",
            label="Video File",
            description="Optional MP4 video file for CAMM extraction (GoPro format).",
            value="",
        ),
        desc.File(
            name="imuBasePath",
            label="IMU Base Path",
            description="Base path for OpenCamera-Sensors CSV files (without extension). "
            "Expected files: {basename}_accel.csv, {basename}_gyro.csv, {basename}_timestamps.csv",
            value="",
        ),
        desc.ChoiceParam(
            name="imuFormat",
            label="IMU Format",
            description="Format of IMU data source.",
            value="opencamera",
            values=["opencamera", "camm"],
            exclusive=True,
        ),
        desc.FloatParam(
            name="gravityFilterCutoff",
            label="Gravity Filter Cutoff (Hz)",
            description="Cutoff frequency for low-pass Butterworth filter used to extract gravity vector.",
            value=0.1,
            range=(0.01, 10.0, 0.01),
        ),
        desc.FloatParam(
            name="samplingRate",
            label="IMU Sampling Rate (Hz)",
            description="Sampling rate of IMU data in Hz. Used for filter design.",
            value=100.0,
            range=(1.0, 1000.0, 1.0),
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
            exclusive=True,
        ),
    ]

    outputs = [
        desc.File(
            name="imuData",
            label="IMU Data",
            description="Processed IMU data in JSON format.",
            value="{nodeCacheFolder}/imu_data.json",
        ),
        desc.File(
            name="gravityVector",
            label="Gravity Vector",
            description="Extracted gravity vector in NPY format (normalized, in world frame).",
            value="{nodeCacheFolder}/gravity_vector.npy",
        ),
    ]

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            logger = chunk.logger

            # Get input parameters
            video_file = chunk.node.videoFile.value
            imu_base_path = chunk.node.imuBasePath.value
            imu_format = chunk.node.imuFormat.value
            gravity_cutoff = chunk.node.gravityFilterCutoff.value
            sampling_rate = chunk.node.samplingRate.value

            # Get output paths
            imu_data_output = chunk.node.attribute("imuData").value
            gravity_vector_output = chunk.node.attribute("gravityVector").value

            # Validate inputs
            if imu_format == "opencamera":
                if not imu_base_path:
                    raise ValueError(
                        "IMU base path is required for OpenCamera format"
                    )

                logger.info(
                    "Loading OpenCamera-Sensors CSV data from: %s",
                    imu_base_path,
                )
                imu_data = load_opencamera_csv(imu_base_path)
                logger.info("Loaded %d IMU samples", len(imu_data))

            elif imu_format == "camm":
                if not video_file:
                    raise ValueError("Video file is required for CAMM format")

                logger.info("Extracting CAMM metadata from: %s", video_file)
                camm_data = detect_camm_in_mp4(video_file)

                if camm_data is None or not camm_data.get("extracted", False):
                    raise RuntimeError(
                        f"Could not extract CAMM data from {video_file}. "
                        "CAMM extraction requires proper MP4 box parsing. "
                        "Please use OpenCamera-Sensors CSV format instead."
                    )

                # TODO: Convert CAMM data to IMUData format
                # For now, raise error as CAMM extraction is not fully implemented
                raise NotImplementedError(
                    "Full CAMM extraction is not yet implemented. "
                    "Please use OpenCamera-Sensors CSV format."
                )
            else:
                raise ValueError(f"Unknown IMU format: {imu_format}")

            # Process IMU data
            logger.info("Processing IMU data...")
            processor = IMUProcessor(imu_data)

            # Extract gravity vector
            logger.info(
                "Extracting gravity vector with cutoff frequency: %.2f Hz",
                gravity_cutoff,
            )
            gravity_vector = processor.extract_gravity_vector(
                cutoff_freq=gravity_cutoff, sampling_rate=sampling_rate
            )

            logger.info("Gravity vector (sensor frame): %s", gravity_vector)

            # Transform to world frame
            gravity_world = transform_android_to_world(gravity_vector)
            logger.info("Gravity vector (world frame): %s", gravity_world)

            # Normalize
            gravity_norm = np.linalg.norm(gravity_world)
            if gravity_norm > 0:
                gravity_world = gravity_world / gravity_norm

            # Save IMU data
            logger.info("Saving IMU data to: %s", imu_data_output)
            os.makedirs(os.path.dirname(imu_data_output), exist_ok=True)
            save_imu_data_json(imu_data, imu_data_output)

            # Save gravity vector
            logger.info("Saving gravity vector to: %s", gravity_vector_output)
            os.makedirs(os.path.dirname(gravity_vector_output), exist_ok=True)
            np.save(gravity_vector_output, gravity_world)

            logger.info("LoadIMUData completed successfully")

        except (
            ValueError,
            RuntimeError,
            NotImplementedError,
            FileNotFoundError,
        ) as e:
            chunk.logger.error("Error in LoadIMUData: %s", str(e))
            raise
        finally:
            chunk.logManager.end()
