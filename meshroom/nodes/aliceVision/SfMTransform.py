__version__ = "3.1"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL

import os.path


class SfMTransform(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmTransform {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
This node allows to change the coordinate system of one SfM scene.

The transformation can be based on:
 * transformation: Apply a given transformation
 * auto_from_cameras: Fit all cameras into a box [-1,1]
 * auto_from_landmarks: Fit all landmarks into a box [-1,1]
 * from_single_camera: Use a specific camera as the origin of the coordinate system
 * from_markers: Align specific markers to custom coordinates
 * from_gps: Align with the gps positions from the image metadata
 * align_ground: Detect ground level and align to it
 * from_lineup: Align using a camera pose (json line up file), tracks and a mesh
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="method",
            label="Transformation Method",
            description="Transformation method:\n"
                        " - transformation: Apply a given transformation.\n"
                        " - manual: Apply the gizmo transformation (show the transformed input).\n"
                        " - auto: Determines scene orientation from the cameras' X axis, determines north and scale from GPS information if available, and defines ground level from the point cloud.\n"
                        " - auto_from_cameras: Defines coordinate system from cameras.\n"
                        " - auto_from_cameras_x_axis: Determines scene orientation from the cameras' X axis.\n"
                        " - auto_from_landmarks: Defines coordinate system from landmarks.\n"
                        " - from_single_camera: Defines the coordinate system from the camera specified by --tranformation.\n"
                        " - from_center_camera: Defines the coordinate system from the camera closest to the center of the reconstruction.\n"
                        " - from_markers: Defines the coordinate system from markers specified by --markers.\n"
                        " - from_gps: Defines coordinate system from GPS metadata.\n"
                        " - from_lineup: Defines coordinate system using lineup json file.\n"
                        " - align_ground: Defines ground level from the point cloud density. It assumes that the scene is oriented.",
            value="auto",
            values=["transformation", "manual", "auto", "auto_from_cameras", "auto_from_cameras_x_axis", "auto_from_landmarks", "from_single_camera", "from_center_camera", "from_markers", "from_gps", "from_lineup", "align_ground"],
        ),
        desc.File(
            name="lineUp",
            label="Line Up File",
            description="LineUp Json file.",
            value="",
            enabled=lambda node: node.method.value == "from_lineup"
        ),
        desc.File(
            name="tracksFile",
            label="Tracks File",
            description="Tracks file for lineup.",
            value="",
            enabled=lambda node: node.method.value == "from_lineup"
        ),
        desc.File(
            name="objectFile",
            label="Mesh File",
            description="Mesh file for lineup.",
            value="",
            enabled=lambda node: node.method.value == "from_lineup"
        ),
        desc.StringParam(
            name="transformation",
            label="Transformation",
            description="Required only for 'transformation' and 'from_single_camera' methods:\n"
                        " - transformation: Align [X,Y,Z] to +Y-axis, rotate around Y by R deg, scale by S; syntax: X,Y,Z;R;S\n"
                        " - from_single_camera: Camera UID or simplified regular expression to match image filepath (like '*camera2*.jpg').",
            value="",
            enabled=lambda node: node.method.value == "transformation" or node.method.value == "from_single_camera" or node.method.value == "auto_from_cameras_x_axis",
        ),
        desc.GroupAttribute(
            name="manualTransform",
            label="Manual Transform (Gizmo)",
            description="Translation, rotation (Euler ZXY) and uniform scale.",
            groupDesc=[
                desc.GroupAttribute(
                    name="manualTranslation",
                    label="Translation",
                    description="Translation in space.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x",
                            label="x",
                            description="X offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="y",
                            label="y",
                            description="Y offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="z",
                            label="z",
                            description="Z offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                    ],
                    joinChar=",",
                ),
                desc.GroupAttribute(
                    name="manualRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler angles.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x",
                            label="x",
                            description="Euler X rotation.",
                            value=0.0,
                            range=(-90.0, 90.0, 1.0),
                        ),
                        desc.FloatParam(
                            name="y",
                            label="y",
                            description="Euler Y rotation.",
                            value=0.0,
                            range=(-180.0, 180.0, 1.0),
                        ),
                        desc.FloatParam(
                            name="z",
                            label="z",
                            description="Euler Z rotation.",
                            value=0.0,
                            range=(-180.0, 180.0, 1.0),
                        ),
                    ],
                    joinChar=",",
                ),
                desc.FloatParam(
                    name="manualScale",
                    label="Scale",
                    description="Uniform scale.",
                    value=1.0,
                    range=(0.0, 20.0, 0.01),
                ),
            ],
            joinChar=",",
            enabled=lambda node: node.method.value == "manual",
        ),
        desc.ChoiceParam(
            name="landmarksDescriberTypes",
            label="Landmarks Describer Types",
            description="Image describer types used to compute the mean of the point cloud (only for 'landmarks' method).",
            values=DESCRIBER_TYPES,
            value=["sift", "dspsift", "akaze"],
            exclusive=False,
            joinChar=",",
        ),
        desc.FloatParam(
            name="scale",
            label="Additional Scale",
            description="Additional scale to apply.",
            value=1.0,
            range=(0.0, 100.0, 0.1),
        ),
        desc.ListAttribute(
            name="markers",
            elementDesc=desc.GroupAttribute(
                name="markerAlign",
                label="Marker Align",
                description="",
                joinChar=":",
                groupDesc=[
                    desc.IntParam(
                        name="markerId",
                        label="Marker",
                        description="Marker ID.",
                        value=0,
                        range=(0, 32, 1),
                    ),
                    desc.GroupAttribute(
                        name="markerCoord",
                        label="Coord",
                        description="Marker coordinates.",
                        joinChar=",",
                        groupDesc=[
                            desc.FloatParam(
                                name="x",
                                label="x",
                                description="X coordinates for the marker.",
                                value=0.0,
                                range=(-2.0, 2.0, 1.0),
                            ),
                            desc.FloatParam(
                                name="y",
                                label="y",
                                description="Y coordinates for the marker.",
                                value=0.0,
                                range=(-2.0, 2.0, 1.0),
                            ),
                            desc.FloatParam(
                                name="z",
                                label="z",
                                description="Z coordinates for the marker.",
                                value=0.0,
                                range=(-2.0, 2.0, 1.0),
                            ),
                        ],
                    ),
                ],
            ),
            label="Markers",
            description="Markers alignment points.",
        ),
        desc.BoolParam(
            name="applyScale",
            label="Scale",
            description="Apply scale transformation.",
            value=True,
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name="applyRotation",
            label="Rotation",
            description="Apply rotation transformation.",
            value=True,
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name="applyTranslation",
            label="Translation",
            description="Apply translation transformation.",
            value=True,
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData File",
            description="Aligned SfMData file.",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "sfmData") + ".abc",
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Poses",
            description="Path to the output SfMData file with cameras (views and poses).",
            value=desc.Node.internalFolder + "cameras.sfm",
        ),
    ]
