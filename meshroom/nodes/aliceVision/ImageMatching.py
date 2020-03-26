__version__ = "1.1"

import os
from meshroom.core import desc


class ImageMatching(desc.CommandLineNode):
    commandLine = 'aliceVision_imageMatching {allParams}'
    size = desc.DynamicNodeSize('input')

    documentation = '''
The goal of this node is to select the image pairs to match. The ambition is to find the images that are looking to the same areas of the scene.
Thanks to this node, the FeatureMatching node will only compute the matches between the selected image pairs.

It provides multiple methods:
 * **VocabularyTree**
It uses image retrieval techniques to find images that share some content without the cost of resolving all feature matches in details.
Each image is represented in a compact image descriptor which allows to compute the distance between all images descriptors very efficiently.
If your scene contains less than "Voc Tree: Minimal Number of Images", all image pairs will be selected.
 * **Sequential**
If your input is a video sequence, you can use this option to link images between them over time.
 * **SequentialAndVocabularyTree**
Combines sequential approach with Voc Tree to enable connections between keyframes at different times.
 * **Exhaustive**
Export all image pairs.
 * **Frustum**
If images have known poses, computes the intersection between cameras frustums to create the list of image pairs.

## Online
[https://alicevision.org/#photogrammetry/image_matching](https://alicevision.org/#photogrammetry/image_matching)
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file .',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors."
        ),
        desc.ChoiceParam(
            name='method',
            label='Method',
            description='Method used to select the image pairs to match.',
            value='VocabularyTree',
            values=['VocabularyTree', 'Sequential', 'SequentialAndVocabularyTree','Exhaustive','Frustum'],
            exclusive=True,
            uid=[0],
        ),
        desc.File(
            name='tree',
            label='Voc Tree: Tree',
            description='Input name for the vocabulary tree file.',
            value=os.environ.get('ALICEVISION_VOCTREE', ''),
            uid=[],
        ),
        desc.File(
            name='weights',
            label='Voc Tree: Weights',
            description='Input name for the weight file, if not provided the weights will be computed on the database built with the provided set.',
            value='',
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='minNbImages',
            label='Voc Tree: Minimal Number of Images',
            description='Minimal number of images to use the vocabulary tree. If we have less features than this threshold, we will compute all matching combinations.',
            value=200,
            range=(0, 500, 1),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='maxDescriptors',
            label='Voc Tree: Max Descriptors',
            description='Limit the number of descriptors you load per image. Zero means no limit.',
            value=500,
            range=(0, 100000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='nbMatches',
            label='Voc Tree: Nb Matches',
            description='The number of matches to retrieve for each image (If 0 it will retrieve all the matches).',
            value=50,
            range=(0, 1000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='nbNeighbors',
            label='Sequential: Nb Neighbors',
            description='The number of neighbors to retrieve for each image (If 0 it will retrieve all the neighbors).',
            value=50,
            range=(0, 1000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output List File',
            description='Filepath to the output file with the list of selected image pairs.',
            value=desc.Node.internalFolder + 'imageMatches.txt',
            uid=[],
        ),
    ]
