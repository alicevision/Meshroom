__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ImageMatching(desc.AVCommandLineNode):
    commandLine = 'aliceVision_imageMatching {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
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
 * **FrustumOrVocabularyTree**
If images have known poses, use frustum intersection else use VocabularuTree.

## Online
[https://alicevision.org/#photogrammetry/image_matching](https://alicevision.org/#photogrammetry/image_matching)
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="Folder containing some extracted features and descriptors.",
                value="",
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors.",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="method",
            label="Method",
            description="Method used to select the image pairs to match:\n"
                        " - VocabularyTree:  It uses image retrieval techniques to find images that share some content without the cost of resolving all \n"
                        "feature matches in details. Each image is represented in a compact image descriptor which allows to compute the distance between all \n"
                        "images descriptors very efficiently. If your scene contains less than 'Voc Tree: Minimal Number of Images', all image pairs will be selected.\n"
                        " - Sequential: If your input is a video sequence, you can use this option to link images between them over time.\n"
                        " - SequentialAndVocabularyTree:  Combines sequential approach with VocTree to enable connections between keyframes at different times.\n"
                        " - Exhaustive: Export all image pairs.\n"
                        " - Frustum: If images have known poses, computes the intersection between cameras frustums to create the list of image pairs.\n"
                        " - FrustumOrVocabularyTree: If images have known poses, use frustum intersection else use VocabularyTree.\n",
            value="SequentialAndVocabularyTree",
            values=["VocabularyTree", "Sequential", "SequentialAndVocabularyTree", "Exhaustive", "Frustum", "FrustumOrVocabularyTree"],
        ),
        desc.File(
            name="tree",
            label="Voc Tree: Tree",
            description="Input name for the vocabulary tree file.",
            value="${ALICEVISION_VOCTREE}",
            invalidate=False,
            enabled=lambda node: "VocabularyTree" in node.method.value,
        ),
        desc.File(
            name="weights",
            label="Voc Tree: Weights",
            description="Input name for the weight file.\n"
                        "If not provided, the weights will be computed on the database built with the provided set.",
            value="",
            advanced=True,
            enabled=lambda node: "VocabularyTree" in node.method.value,
        ),
        desc.IntParam(
            name="minNbImages",
            label="Voc Tree: Minimum Number Of Images",
            description="Minimum number of images to use the vocabulary tree.\n"
                        "If we have less features than this threshold, we will compute all matching combinations.",
            value=200,
            range=(0, 500, 1),
            advanced=True,
            enabled=lambda node: "VocabularyTree" in node.method.value,
        ),
        desc.IntParam(
            name="maxDescriptors",
            label="Voc Tree: Max Descriptors",
            description="Limit the number of descriptors you load per image. 0 means no limit.",
            value=500,
            range=(0, 100000, 1),
            advanced=True,
            enabled=lambda node: "VocabularyTree" in node.method.value,
        ),
        desc.IntParam(
            name="nbMatches",
            label="Voc Tree: Nb Matches",
            description="The number of matches to retrieve for each image. (If 0, it will retrieve all the matches).",
            value=40,
            range=(0, 1000, 1),
            advanced=True,
            enabled=lambda node: "VocabularyTree" in node.method.value,
        ),
        desc.IntParam(
            name="nbNeighbors",
            label="Sequential: Nb Neighbors",
            description="The number of neighbors to retrieve for each image. (If 0, it will retrieve all the neighbors).",
            value=5,
            range=(0, 1000, 1),
            advanced=True,
            enabled=lambda node: "Sequential" in node.method.value,
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
            label="Image Pairs",
            description="Filepath to the output file with the list of selected image pairs.",
            value=desc.Node.internalFolder + "imageMatches.txt",
        ),
    ]
