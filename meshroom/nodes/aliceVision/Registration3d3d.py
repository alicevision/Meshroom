from meshroom.core import desc


class Registration3d3d(desc.CommandLineNode):
    commandLine = 'aliceVision_3d3dRegistration {allParams}'

    inputs = [
        desc.File(
            name='sourceFile',
            label='Source File',
            description="""Path to file source (moving) 3D model.""",
            value='',
            uid=[0],
            ),
        desc.File(
            name='targetFile',
            label='Target File',
            description="""Path to the target (fixed) 3D model.""",
            value='',
            uid=[0],
            ),
        desc.FloatParam(
            name='scaleRatio',
            label='Scale Ratio',
            description="""Scale ratio between the two 3D models (= target size / source size)""",
            value=1.0,
            range=(1.0, 100.0, 1.0),
            uid=[0],
            ),
        desc.FloatParam(
            name='sourceMeasurement',
            label='Source Measurement',
            description="Measurement made ont the source 3D model (same unit as 'targetMeasurement'). \n"
                        "It allows to compute the scale ratio between 3D models.",
            value=1,
            range=(1.0, 10000.0, 1.0),
            uid=[0],
            ),
        desc.FloatParam(
            name='targetMeasurement',
            label='Target Measurement',
            description="Measurement made ont the target 3D model (same unit as 'sourceMeasurement').\n"
                        "It allows to compute the scale ratio between 3D models.",
            value=1,
            range=(1.0, 10000.0, 1.0),
            uid=[0],
            ),
        desc.FloatParam(
            name='voxelSize',
            label='Voxel Size',
            description="""Size of the voxel grid applied on each 3D model to downsample them. \n
                        Downsampling reduces computing duration.""",
            value=0.1,
            range=(0.1, 10.0, 0.1),
            uid=[0],
            ),
        desc.BoolParam(
            name='showPipeline',
            label='Show Pipeline',
            description="""To enable the visualization of each step of the pipeline in external windows.""",
            value=False,
            uid=[],
            ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description="""verbosity level (fatal, error, warning, info, debug, trace).""",
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='outputFile',
            label='Output File',
            description="""Path to save the transformed source 3D model.""",
            value=desc.Node.internalFolder + 'aligned.ply',
            uid=[],
            ),
    ]
