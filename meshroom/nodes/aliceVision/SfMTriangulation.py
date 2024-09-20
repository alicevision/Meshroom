__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class SfMTriangulation(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmTriangulation {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''
This node perfoms keypoint triangulation on its input data.
Contrary to the StructureFromMotion node, this node does not infer the camera poses, therefore they must be given in the SfMData input.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="SfMData file. Must contain the camera calibration.",
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
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="Folder in which some computed matches are stored.",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored.",
            exposed=True,
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
        desc.IntParam(
            name="maxNumberOfMatches",
            label="Maximum Number Of Matches",
            description="Maximum number of matches per image pair (and per feature type).\n"
                        "This can be useful to have a quick reconstruction overview.\n"
                        "0 means no limit.",
            value=0,
            range=(0, 50000, 1),
        ),
        desc.IntParam(
            name="minNumberOfMatches",
            label="Minimum Number Of Matches",
            description="Minimum number of matches per image pair (and per feature type).\n"
                        "This can be useful to have a meaningful reconstruction with accurate keypoints.\n"
                        "0 means no limit.",
            value=0,
            range=(0, 50000, 1),
        ),
        desc.IntParam(
            name="minNumberOfObservationsForTriangulation",
            label="Min Observations For Triangulation",
            description="Minimum number of observations to triangulate a point.\n"
                        "Setting it to 3 (or more) reduces drastically the noise in the point cloud,\n"
                        "but the number of final poses is a little bit reduced\n"
                        "(from 1.5% to 11% on the tested datasets).",
            value=2,
            range=(2, 10, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="minAngleForTriangulation",
            label="Min Angle For Triangulation",
            description="Minimum angle for triangulation.",
            value=3.0,
            range=(0.1, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="minAngleForLandmark",
            label="Min Angle For Landmark",
            description="Minimum angle for landmark.",
            value=2.0,
            range=(0.1, 10.0, 0.1),
            advanced=True,
        ),
        desc.BoolParam(
            name="useRigConstraint",
            label="Use Rig Constraint",
            description="Enable/Disable rig constraint.",
            value=True,
            advanced=True,
        ),
        desc.IntParam(
            name="rigMinNbCamerasForCalibration",
            label="Min Nb Cameras For Rig Calibration",
            description="Minimum number of cameras to start the calibration of the rig.",
            value=20,
            range=(1, 50, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="computeStructureColor",
            label="Compute Structure Color",
            description="Enable/Disable color computation of each 3D point.",
            value=True,
        ),
        desc.ChoiceParam(
            name="interFileExtension",
            label="Inter File Extension",
            description="Extension of the intermediate file export.",
            value=".abc",
            values=[".abc", ".ply"],
            invalidate=False,
            advanced=True,
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
            name="extraInfoFolder",
            label="Folder",
            description="Folder for intermediate reconstruction files and additional reconstruction information files.",
            value=desc.Node.internalFolder,
        ),
    ]
