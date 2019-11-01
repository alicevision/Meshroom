__version__ = "1.1"

from meshroom.core import desc


class SfMTransform(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_sfmTransform {allParams}'
    size = desc.DynamicNodeSize('input')

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
                        " * auto_from_cameras: Use cameras\n"
                        " * auto_from_landmarks: Use landmarks\n"
                        " * from_single_camera: Use a specific camera as the origin of the coordinate system\n"
                        " * from_markers: Align specific markers to custom coordinates",
            value='auto_from_landmarks',
            values=['transformation', 'auto_from_cameras', 'auto_from_landmarks', 'from_single_camera', 'from_markers'],
            exclusive=True,
            uid=[0],
        ),
        desc.StringParam(
            name='transformation',
            label='Transformation',
            description="Required only for 'transformation' and 'from_single_camera' methods:\n"
                        " * transformation: Align [X,Y,Z] to +Y-axis, rotate around Y by R deg, scale by S; syntax: X,Y,Z;R;S\n"
                        " * from_single_camera: Camera UID or image filename",
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='landmarksDescriberTypes',
            label='Landmarks Describer Types',
            description='Image describer types used to compute the mean of the point cloud. (only for "landmarks" method).',
            value=['sift', 'akaze'],
            values=['sift', 'sift_float', 'sift_upright', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv'],
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
            uid=[0]
        ),
        desc.BoolParam(
            name='applyRotation',
            label='Rotation',
            description='Apply rotation transformation.',
            value=True,
            uid=[0]
        ),
        desc.BoolParam(
            name='applyTranslation',
            label='Translation',
            description='Apply translation transformation.',
            value=True,
            uid=[0]
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
            label='Output',
            description='''Aligned SfMData file .''',
            value=desc.Node.internalFolder + 'transformedSfM.abc',
            uid=[],
        ),
    ]
