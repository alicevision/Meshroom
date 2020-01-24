__version__ = "1.0"

from meshroom.core import desc


class HDRIstitching(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_fisheyeProjection {allParams}'

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name='inputFile',
                label='Input File/Folder',
                description="",
                value='',
                uid=[0],
            ),
            name='input',
            label='Input Folder',
            description="List of fisheye images or folder containing them."
        ),
        desc.FloatParam(
            name='blurWidth',
            label='Blur Width',
            description="Blur width of alpha channel for all fisheye (between 0 and 1). \n"
                        "Determine the transitions sharpness.",
            value=0.2,
            range=(0, 1, 0.1),
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name='imageXRotation',
                label='Image X Rotation',
                description="",
                value=0,
                range=(-20, 20, 1),
                uid=[0],
            ),
            name='xRotation',
            label='X Rotations',
            description="Rotations in degree on axis X (horizontal axis) for each image.",
        ),
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name='imageYRotation',
                label='Image Y Rotation',
                description="",
                value=0,
                range=(-30, 30, 5),
                uid=[0],
            ),
            name='yRotation',
            label='Y Rotations',
            description="Rotations in degree on axis Y (vertical axis) for each image.",
        ),
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name='imageZRotation',
                label='Image Z Rotation',
                description="",
                value=0,
                range=(-10, 10, 1),
                uid=[0],
            ),
            name='zRotation',
            label='Z Rotations',
            description="Rotations in degree on axis Z (depth axis) for each image.",
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Panorama',
            description="Output folder for panorama",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]