"""
MrIMU - IMU Integration Plugin for Meshroom
"""

__version__ = "1.0.0"

__author__ = "Meshroom Community"

__license__ = "MPL-2.0"


def register(registry):
    """Register MrIMU nodes"""
    from .meshroom.nodes import LoadIMUData, ApplyIMUConstraints

    registry.registerNode(LoadIMUData)
    registry.registerNode(ApplyIMUConstraints)

