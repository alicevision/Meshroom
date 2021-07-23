__version__ = "3.0"

from meshroom.core import desc

import os.path


class SfMTransform(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_sfmTransform {allParams}'
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

'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file .''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='method',
            label='Transformation Method',
            description="Transformation method:\n"
                        " * transformation: Apply a given transformation\n"
                        " * manual: Apply the gizmo transformation (show the transformed input)\n"
                        " * auto_from_cameras: Use cameras\n"
                        " * auto_from_landmarks: Use landmarks\n"
                        " * from_single_camera: Use a specific camera as the origin of the coordinate system\n"
                        " * from_center_camera: Use the center camera as the origin of the coordinate system\n"
                        " * from_markers: Align specific markers to custom coordinates\n"
                        " * from_gps: Align with the gps positions from the image metadata",
            value='auto_from_landmarks',
            values=['transformation', 'manual', 'auto_from_cameras', 'auto_from_landmarks', 'from_single_camera', 'from_center_camera', 'from_markers', 'from_gps'],
            exclusive=True,
            uid=[0],
        ),
        desc.StringParam(
            name='transformation',
            label='Transformation',
            description="Required only for 'transformation' and 'from_single_camera' methods:\n"
                        " * transformation: Align [X,Y,Z] to +Y-axis, rotate around Y by R deg, scale by S; syntax: X,Y,Z;R;S\n"
                        " * from_single_camera: Camera UID or simplified regular expression to match image filepath (like '*camera2*.jpg')",
            value='',
            uid=[0],
            enabled=lambda node: node.method.value == "transformation" or node.method.value == "from_single_camera",
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
                            name="x", label="x", description="X Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        )
                    ],
                    joinChar=","
                ),
                desc.GroupAttribute(
                    name="manualRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler degrees.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="Euler X Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-90.0, 90.0, 1)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Euler Y Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Euler Z Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        )
                    ],
                    joinChar=","
                ),
                desc.FloatParam(
                    name="manualScale",
                    label="Scale",
                    description="Uniform Scale.",
                    value=1.0,
                    uid=[0],
                    range=(0.0, 20.0, 0.01)
                )
            ],
            joinChar=",",
            enabled=lambda node: node.method.value == "manual",
        ),
        desc.ChoiceParam(
            name='landmarksDescriberTypes',
            label='Landmarks Describer Types',
            description='Image describer types used to compute the mean of the point cloud. (only for "landmarks" method).',
            value=['sift', 'dspsift', 'akaze'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5', 'unknown'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.FloatParam(
            name='scale',
            label='Additional Scale',
            description='Additional scale to apply.',
            value=1.0,
            range=(0.0, 100.0, 0.1),
            uid=[0],
        ),
        desc.ListAttribute(
            name="markers",
            elementDesc=desc.GroupAttribute(name="markerAlign", label="Marker Align", description="", joinChar=":", groupDesc=[
                desc.IntParam(name="markerId", label="Marker", description="Marker Id", value=0, uid=[0], range=(0, 32, 1)),
                desc.GroupAttribute(name="markerCoord", label="Coord", description="", joinChar=",", groupDesc=[
                    desc.FloatParam(name="x", label="x", description="", value=0.0, uid=[0], range=(-2.0, 2.0, 1.0)),
                    desc.FloatParam(name="y", label="y", description="", value=0.0, uid=[0], range=(-2.0, 2.0, 1.0)),
                    desc.FloatParam(name="z", label="z", description="", value=0.0, uid=[0], range=(-2.0, 2.0, 1.0)),
                ])
            ]),
            label="Markers",
            description="Markers alignment points",
        ),
        desc.BoolParam(
            name='applyScale',
            label='Scale',
            description='Apply scale transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name='applyRotation',
            label='Rotation',
            description='Apply rotation transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.BoolParam(
            name='applyTranslation',
            label='Translation',
            description='Apply translation transformation.',
            value=True,
            uid=[0],
            enabled=lambda node: node.method.value != "manual",
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output SfMData File',
            description='''Aligned SfMData file .''',
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or 'sfmData') + '.abc',
            uid=[],
        ),
        desc.File(
            name='outputViewsAndPoses',
            label='Output Poses',
            description='''Path to the output sfmdata file with cameras (views and poses).''',
            value=desc.Node.internalFolder + 'cameras.sfm',
            uid=[],
        ),
    ]
