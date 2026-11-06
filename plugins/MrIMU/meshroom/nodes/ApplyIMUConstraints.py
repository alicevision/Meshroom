__version__ = "1.0.0"

import json
import os

import numpy as np

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

try:
    # Try relative import first (when loaded as plugin)
    from ..imu_utils import IMUProcessor, load_imu_data_json
except ImportError:
    # Fallback: import directly from file path
    import sys
    import os
    import importlib.util
    plugin_meshroom_dir = os.path.dirname(os.path.dirname(__file__))
    imu_utils_path = os.path.join(plugin_meshroom_dir, "imu_utils.py")
    spec = importlib.util.spec_from_file_location("imu_utils", imu_utils_path)
    imu_utils = importlib.util.module_from_spec(spec)
    sys.modules["imu_utils"] = imu_utils
    spec.loader.exec_module(imu_utils)
    IMUProcessor = imu_utils.IMUProcessor
    load_imu_data_json = imu_utils.load_imu_data_json


class ApplyIMUConstraints(desc.Node):
    """
    Apply IMU orientation constraints to StructureFromMotion camera poses.

    This node takes the SfM scene file from Meshroom's StructureFromMotion node
    and applies IMU-based orientation constraints to improve camera pose estimation,
    especially for maintaining vertical axis stability.
    """

    category = "IMU"
    documentation = """
Apply IMU constraints to SfM camera poses.

**Inputs:**
- SfM scene file (JSON format from StructureFromMotion node)
- IMU data (JSON format from LoadIMUData node)
- IMU weight: Balance between optical (0.0) and IMU (1.0) data
- Lock Z-axis: Keep vertical axis aligned with gravity

**Outputs:**
- Corrected SfM scene file with IMU-adjusted camera poses
"""

    inputs = [
        desc.File(
            name="sfmScene",
            label="SfM Scene",
            description="Input SfM scene file from StructureFromMotion node.",
            value="",
        ),
        desc.File(
            name="imuData",
            label="IMU Data",
            description="Processed IMU data JSON file from LoadIMUData node.",
            value="",
        ),
        desc.FloatParam(
            name="imuWeight",
            label="IMU Weight",
            description="Weight for IMU data influence (0.0 = optical only, 1.0 = IMU only).",
            value=0.5,
            range=(0.0, 1.0, 0.01),
        ),
        desc.BoolParam(
            name="lockZAxis",
            label="Lock Z-Axis to Gravity",
            description="Constrain vertical axis to align with gravity direction.",
            value=True,
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
            name="outputScene",
            label="Output Scene",
            description="Corrected SfM scene file with IMU-adjusted camera poses.",
            value="{nodeCacheFolder}/sfm_imu_corrected.json",
        ),
    ]

    def load_sfm_scene(self, scene_path: str) -> dict:
        """
        Load SfM scene JSON file.

        Args:
            scene_path: Path to SfM scene JSON file

        Returns:
            Dictionary containing scene data
        """
        with open(scene_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_sfm_scene(self, scene_data: dict, output_path: str):
        """
        Save SfM scene JSON file.

        Args:
            scene_data: Dictionary containing scene data
            output_path: Path to output JSON file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scene_data, f, indent=2)

    def extract_camera_poses(self, scene_data: dict) -> dict:
        """
        Extract camera poses from SfM scene.

        Args:
            scene_data: SfM scene dictionary

        Returns:
            Dictionary mapping view IDs to camera poses (rotation + translation)
        """
        poses = {}

        # SfM scene structure may vary, try common formats
        if "views" in scene_data and "poses" in scene_data:
            for view_id, view_data in scene_data["views"].items():
                pose_id = view_data.get("poseId")
                if pose_id is not None and pose_id in scene_data["poses"]:
                    pose = scene_data["poses"][pose_id]
                    poses[view_id] = pose

        return poses

    def apply_imu_constraint_to_pose(
        self,
        pose: dict,
        imu_orientation: np.ndarray,
        imu_weight: float,
        lock_z: bool,
    ) -> dict:
        """
        Apply IMU constraint to a single camera pose.

        Args:
            pose: Camera pose dictionary (with rotation and center)
            imu_orientation: IMU-derived rotation matrix (3x3)
            imu_weight: Weight for IMU influence (0.0 to 1.0)
            lock_z: Whether to lock Z-axis to gravity

        Returns:
            Modified pose dictionary
        """
        # Extract current pose rotation
        # SfM typically stores rotation as a 3x3 matrix or quaternion
        # We'll assume 3x3 matrix format for now

        if "rotation" in pose:
            current_rotation = np.array(pose["rotation"])
        elif "transform" in pose:
            # Extract rotation from 4x4 transform matrix
            transform = np.array(pose["transform"])
            current_rotation = transform[:3, :3]
        else:
            # No rotation found, use identity
            current_rotation = np.eye(3)

        # Blend rotations based on IMU weight
        if imu_weight > 0.0:
            if lock_z:
                # Lock Z-axis: align Z-axis of current rotation with IMU Z-axis
                imu_z = imu_orientation[:, 2]  # Z-axis of IMU orientation
                current_z = current_rotation[
                    :, 2
                ]  # Z-axis of current rotation

                # Project current Z onto plane perpendicular to IMU Z
                # Then align with IMU Z
                if imu_weight >= 1.0:
                    # Full IMU constraint
                    new_z = imu_z
                else:
                    # Blend between current and IMU Z
                    new_z = (1.0 - imu_weight) * current_z + imu_weight * imu_z
                    new_z = new_z / np.linalg.norm(new_z)

                # Reconstruct rotation matrix with new Z-axis
                # Keep X and Y axes as orthogonal to new Z
                if abs(new_z[0]) < 0.9:
                    new_x = np.array([1, 0, 0])
                else:
                    new_x = np.array([0, 1, 0])

                new_x = new_x - np.dot(new_x, new_z) * new_z
                new_x = new_x / np.linalg.norm(new_x)
                new_y = np.cross(new_z, new_x)
                new_y = new_y / np.linalg.norm(new_y)

                new_rotation = np.column_stack([new_x, new_y, new_z])
            else:
                # Blend full rotations
                new_rotation = (
                    1.0 - imu_weight
                ) * current_rotation + imu_weight * imu_orientation

                # Orthonormalize
                U, _, Vt = np.linalg.svd(new_rotation)
                new_rotation = U @ Vt
        else:
            new_rotation = current_rotation

        # Update pose
        new_pose = pose.copy()
        if "rotation" in new_pose:
            new_pose["rotation"] = new_rotation.tolist()
        elif "transform" in new_pose:
            transform = np.array(new_pose["transform"])
            transform[:3, :3] = new_rotation
            new_pose["transform"] = transform.tolist()
        else:
            new_pose["rotation"] = new_rotation.tolist()

        return new_pose

    def processChunk(self, chunk):
        try:
            chunk.logManager.start(chunk.node.verboseLevel.value)
            logger = chunk.logger

            # Get input parameters
            sfm_scene_path = chunk.node.sfmScene.value
            imu_data_path = chunk.node.imuData.value
            imu_weight = chunk.node.imuWeight.value
            lock_z_axis = chunk.node.lockZAxis.value

            # Get output path
            output_scene_path = chunk.node.attribute("outputScene").value

            # Validate inputs
            if not sfm_scene_path or not os.path.exists(sfm_scene_path):
                raise FileNotFoundError(
                    f"SfM scene file not found: {sfm_scene_path}"
                )

            if not imu_data_path or not os.path.exists(imu_data_path):
                raise FileNotFoundError(
                    f"IMU data file not found: {imu_data_path}"
                )

            logger.info("Loading SfM scene from: %s", sfm_scene_path)
            scene_data = self.load_sfm_scene(sfm_scene_path)

            logger.info("Loading IMU data from: %s", imu_data_path)
            imu_data = load_imu_data_json(imu_data_path)

            # Process IMU data to get orientation
            logger.info("Processing IMU data to extract orientation...")
            processor = IMUProcessor(imu_data)

            if lock_z_axis:
                imu_orientation = processor.constrain_z_axis_to_gravity()
                logger.info("Z-axis locked to gravity direction")
            else:
                imu_orientation = processor.estimate_orientation()

            logger.info("IMU weight: %.2f", imu_weight)
            logger.info("IMU orientation matrix:\n%s", imu_orientation)

            # Extract camera poses
            poses = self.extract_camera_poses(scene_data)
            logger.info("Found %d camera poses to correct", len(poses))

            # Apply IMU constraints to each pose
            corrected_count = 0
            for view_id, pose in poses.items():
                try:
                    corrected_pose = self.apply_imu_constraint_to_pose(
                        pose, imu_orientation, imu_weight, lock_z_axis
                    )

                    # Update scene data
                    if "poses" in scene_data:
                        pose_id = (
                            scene_data["views"].get(view_id, {}).get("poseId")
                        )
                        if pose_id is not None:
                            scene_data["poses"][pose_id] = corrected_pose
                            corrected_count += 1
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(
                        "Failed to correct pose for view %s: %s", view_id, e
                    )
                    continue

            logger.info("Corrected %d camera poses", corrected_count)

            # Save corrected scene
            logger.info("Saving corrected scene to: %s", output_scene_path)
            self.save_sfm_scene(scene_data, output_scene_path)

            logger.info("ApplyIMUConstraints completed successfully")

        except (
            FileNotFoundError,
            ValueError,
            KeyError,
            json.JSONDecodeError,
        ) as e:
            chunk.logger.error("Error in ApplyIMUConstraints: %s", str(e))
            raise
        finally:
            chunk.logManager.end()
