__version__ = "1.0"


from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class GlobalSfM(desc.AVCommandLineNode):
    commandLine = "aliceVision_globalSfM {allParams}"
    size = desc.DynamicNodeSize("input")

    category = "Sparse Reconstruction"
    documentation = """
Performs the Structure-From-Motion with a global approach.
It is known to be faster but less robust to challenging datasets than the Incremental approach.
"""

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
                description="Folder containing some extracted features.",
                value="",
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="Folder containing some computed matches.",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored.",
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="rotationAveraging",
            label="Rotation Averaging Method",
            description="Method for rotation averaging:\n"
                        " - L1 minimization\n"
                        " - L2 minimization",
            values=["L1_minimization", "L2_minimization"],
            value="L2_minimization",
        ),
        desc.ChoiceParam(
            name="translationAveraging",
            label="Translation Averaging Method",
            description="Method for translation averaging:\n"
                        " - L1 minimization\n"
                        " - L2 minimization of sum of squared Chordal distances\n"
                        " - L1 soft minimization",
            values=["L1_minimization", "L2_minimization", "L1_soft_minimization"],
            value="L1_soft_minimization",
        ),
        desc.BoolParam(
            name="lockAllIntrinsics",
            label="Lock All Intrinsic Camera Parameters",
            description="Force to keep all the intrinsics parameters of the cameras (focal length, \n"
                        "principal point, distortion if any) constant during the reconstruction.\n"
                        "This may be helpful if the input cameras are already fully calibrated.",
            value=False,
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
            label="SfMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfm.abc",
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Output Poses",
            description="Path to the output SfMData file with cameras (views and poses).",
            value=desc.Node.internalFolder + "cameras.sfm",
        ),
        desc.File(
            name="extraInfoFolder",
            label="Folder",
            description="Folder for intermediate reconstruction files and additional reconstruction information files.",
            value=desc.Node.internalFolder,
        ),
    ]
