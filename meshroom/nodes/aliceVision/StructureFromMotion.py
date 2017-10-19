import sys
from meshroom.core import desc


class StructureFromMotion(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_incrementalSfM {allParams}'

    input = desc.File(
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    output = desc.File(
            label='Output SfM data file',
            description='''Path to the output sfmdata file''',
            value='{cache}/{nodeType}/{uid0}/sfm.abc',
            uid=[],
            isOutput=True,
            )
    extraInfoDirectory = desc.File(
            label='Output',
            description='''Directory for intermediate reconstruction files and additional reconstruction information files.''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[0],
            isOutput=True,
    )
    featuresDirectory = desc.File(
            label='Features Directory',
            description='''Path to a directory containing the extracted features.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    matchesDirectory = desc.File(
            label='Matches Directory',
            description='''Path to a directory in which computed matches are stored. Optional parameters:''',
            value='',
            uid=[0],
            isOutput=False,
            )
    describerTypes = desc.StringParam(
            label='Describer Types',
            description='''Describer types to use to describe an image:''',
            value='SIFT',
            uid=[0],
            )
    interFileExtension = desc.File(
            label='Inter File Extension',
            description='''Extension of the intermediate file export.''',
            value='.ply',
            uid=[0],
            isOutput=False,
            )
    minInputTrackLength = desc.IntParam(
            label='Min Input Track Length',
            description='''Minimum track length in input of SfM''',
            value=2,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    cameraModel = desc.ChoiceParam(
            label='Camera Model',
            description='''* 1: Pinhole * 2: Pinhole radial 1 * 3: Pinhole radial 3''',
            value=3,
            values=['1', '2', '3'],
            exclusive=True,
            uid=[0],
            )
    initialPairA = desc.File(
            label='Initial Pair A',
            description='''filename of the first image (without path).''',
            value='',
            uid=[0],
            isOutput=False,
            )
    initialPairB = desc.File(
            label='Initial Pair B',
            description='''filename of the second image (without path).''',
            value='',
            uid=[0],
            isOutput=False,
            )
    refineIntrinsics = desc.ChoiceParam(
            label='Refine Intrinsics',
            description='''intrinsic parameters. Log parameters:''',
            value=0,
            values=[0, 1],
            exclusive=True,
            uid=[0],
            )
    verboseLevel = desc.ChoiceParam(
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
            )