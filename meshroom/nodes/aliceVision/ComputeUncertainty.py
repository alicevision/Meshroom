from meshroom.core import desc


class ComputeUncertainty(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_utils_computeUncertainty {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file to align.''',
            value="",
            uid=[0],
            ),
        desc.ChoiceParam(
            name='algorithm',
            label='Algorithm',
            description='''Algorithm.''',
            value="TAYLOR_EXPANSION",
            values=["SVD_QR_ITERATION", "SVD_DEVIDE_AND_CONQUER", "TAYLOR_EXPANSION"],
            exclusive=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='debug',
            label='Debug',
            description='''Enable creation of debug files in the current folder.''',
            value=False,
            uid=[],
            ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value="info",
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
            ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Output SfMData scene.''',
            value="{cache}/{nodeType}/{uid0}/sfm.abc",
            uid=[],
            ),
        desc.File(
            name='outputCov',
            label='Output Cov',
            description='''Output covariances file.''',
            value="{cache}/{nodeType}/{uid0}/uncertainty.cov",
            uid=[],
            ),
    ]
