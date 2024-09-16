__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class CameraRigLocalization(desc.AVCommandLineNode):
    commandLine = 'aliceVision_rigLocalization {allParams}'

    category = 'Utils'
    documentation = '''
    '''

    inputs = [
        desc.File(
            name="sfmdata",
            label="SfMData",
            description="The input SfMData file.",
            value="",
        ),
        desc.File(
            name="mediapath",
            label="Media Path",
            description="The path to the video file, the folder of the image sequence or a text file (one image path per line) for each camera of the rig (eg. --mediapath /path/to/cam1.mov /path/to/cam2.mov).",
            value="",
        ),
        desc.File(
            name="calibration",
            label="Rig Calibration File",
            description="The file containing the calibration data for the rig (subposes).",
            value="",
        ),
        desc.File(
            name="cameraIntrinsics",
            label="Camera Intrinsics",
            description="The intrinsics calibration file for each camera of the rig (eg. --cameraIntrinsics /path/to/calib1.txt /path/to/calib2.txt).",
            value="",
        ),
        desc.File(
            name="descriptorPath",
            label="Descriptor Path",
            description="Folder containing the .desc.",
            value="",
        ),
        desc.ChoiceParam(
            name="matchDescTypes",
            label="Match Describer Types",
            description="The describer types to use for the matching.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="preset",
            label="Preset",
            description="Preset for the feature extractor when localizing a new image (low, medium, normal, high, ultra).",
            value="normal",
            values=["low", "medium", "normal", "high", "ultra"],
        ),
        desc.ChoiceParam(
            name="resectionEstimator",
            label="Resection Estimator",
            description="The type of *sac framework to use for resection (acransac, loransac).",
            value="acransac",
            values=["acransac", "loransac"],
        ),
        desc.ChoiceParam(
            name="matchingEstimator",
            label="Matching Estimator",
            description="The type of *sac framework to use for matching (acransac, loransac).",
            value="acransac",
            values=["acransac", "loransac"],
        ),
        desc.StringParam(
            name="refineIntrinsics",
            label="Refine Intrinsics",
            description="Enable/Disable camera intrinsics refinement for each localized image.",
            value="",
        ),
        desc.FloatParam(
            name="reprojectionError",
            label="Reprojection Error",
            description="Maximum reprojection error (in pixels) allowed for resectioning.\n"
                        "If set to 0, it lets the ACRansac select an optimal value.",
            value=4.0,
            range=(0.0, 10.0, 0.1),
        ),
        desc.BoolParam(
            name="useLocalizeRigNaive",
            label="Use Localize Rig Naive",
            description="Enable/Disable the naive method for rig localization: naive method tries to localize each camera separately.",
            value=False,
        ),
        desc.FloatParam(
            name="angularThreshold",
            label="Angular Threshold",
            description="The maximum angular threshold in degrees between feature bearing vector and 3D point direction. Used only with the opengv method.",
            value=0.1,
            range=(0.0, 10.0, 0.01),
        ),
        desc.File(
            name="voctree",
            label="Voctree",
            description="[voctree] Filename for the vocabulary tree.""",
            value="${ALICEVISION_VOCTREE}",
        ),
        desc.File(
            name="voctreeWeights",
            label="Voctree Weights",
            description="[voctree] Filename for the vocabulary tree weights.",
            value="",
        ),
        desc.ChoiceParam(
            name="algorithm",
            label="Algorithm",
            description="[voctree] Algorithm type: {FirstBest, AllResults}.",
            value="AllResults",
            values=["FirstBest", "AllResults"],
        ),
        desc.IntParam(
            name="nbImageMatch",
            label="Nb Image Match",
            description="[voctree] Number of images to retrieve in the database.",
            value=4,
            range=(0, 100, 1),
        ),
        desc.IntParam(
            name="maxResults",
            label="Max Results",
            description="[voctree] For algorithm AllResults, it stops the image matching when this number of matched images is reached.\n"
                        "If set to 0, it is ignored.",
            value=10,
            range=(0, 100, 1),
        ),
        desc.FloatParam(
            name="matchingError",
            label="Matching Error",
            description="[voctree] Maximum matching error (in pixels) allowed for image matching with geometric verification.\n"
                        "If set to 0, it lets the ACRansac select an optimal value.",
            value=4.0,
            range=(0.0, 10.0, 0.1),
        ),
        desc.IntParam(
            name="nNearestKeyFrames",
            label="N Nearest Key Frames",
            description="[cctag] Number of images to retrieve in database.",
            value=5,
            range=(0, 50, 1),
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
            name="outputAlembic",
            label="Alembic",
            description="Filename for the SfMData export file (where camera poses will be stored).",
            value=desc.Node.internalFolder + "trackedcameras.abc",
        ),
    ]
