import sys
from meshroom.core import desc


class ImageMatching(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_imageMatching {allParams}'

    input = desc.File(
            label='Input',
            description='''SfMData file or filepath to a simple text file with one image filepath per line, or path to the descriptors folder.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    featuresDirectory = desc.File(
            label='Features Directory',
            description='''Directory containing the extracted features and descriptors. By default, it is the directory containing the SfMData.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    tree = desc.File(
            label='Tree',
            description='''Input name for the vocabulary tree file.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    output = desc.File(
            label='Output',
            description='''Filepath to the output file with the list of selected image pairs.''',
            value='{cache}/{nodeType}/{uid0}/imageMatches.txt',
            uid=[],
            isOutput=True,
            )
    maxDescriptors = desc.IntParam(
            label='Max Descriptors',
            description='''Limit the number of descriptors you load per image. Zero means no limit.''',
            value=500,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    nbMatches = desc.IntParam(
            label='Nb Matches',
            description='''The number of matches to retrieve for each image (If 0 it will retrieve all the matches).''',
            value=50,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    weights = desc.File(
            label='Weights',
            description='''Input name for the weight file, if not provided the weights will be computed on the database built with the provided set. Log parameters:''',
            value='',
            uid=[0],
            isOutput=False,
            )
    verboseLevel = desc.ChoiceParam(
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[0],
            )