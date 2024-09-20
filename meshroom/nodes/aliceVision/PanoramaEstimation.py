__version__ = "1.0"

import json
import os

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class PanoramaEstimation(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaEstimation {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Panorama HDR'
    documentation = '''
Estimate relative camera rotations between input images.
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
                description="Folder containing some extracted features.",
                value="",
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features.",
            exposed=True,
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="Folder containing some matches.",
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
            value=["sift"],
            exclusive=False,
            joinChar=",",
            exposed=True,
        ),
        desc.FloatParam(
            name="offsetLongitude",
            label="Longitude Offset",
            description="Offset to the panorama longitude (in degrees).",
            value=0.0,
            range=(-180.0, 180.0, 1.0),
        ),
        desc.FloatParam(
            name="offsetLatitude",
            label="Latitude Offset",
            description="Offset to the panorama latitude (in degrees).",
            value=0.0,
            range=(-90.0, 90.0, 1.0),
        ),
        desc.ChoiceParam(
            name="rotationAveraging",
            label="Rotation Averaging Method",
            description="Method for rotation averaging :\n"
                        " - L1 minimization\n"
                        " - L2 minimization",
            values=["L1_minimization", "L2_minimization"],
            value="L2_minimization",
            advanced=True,
        ),
        desc.ChoiceParam(
            name="relativeRotation",
            label="Relative Rotation Method",
            description="Method for relative rotation :\n"
                        " - from essential matrix\n"
                        " - from homography matrix\n"
                        " - from rotation matrix",
            values=["essential_matrix", "homography_matrix", "rotation_matrix"],
            value="rotation_matrix",
            advanced=True,
        ),
        desc.BoolParam(
            name="rotationAveragingWeighting",
            label="Rotation Averaging Weighting",
            description="Rotation averaging weighting based on the number of feature matches.",
            value=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="filterMatches",
            label="Filter Matches",
            description="Filter the matches.",
            value=False,
        ),
        desc.BoolParam(
            name="refine",
            label="Refine",
            description="Refine camera relative poses, points and optionally internal camera parameters.",
            value=True,
        ),
        desc.BoolParam(
            name="lockAllIntrinsics",
            label="Lock All Intrinsics",
            description="Force to keep all the intrinsics parameters of the cameras (focal length, \n"
                        "principal point, distortion if any) constant during the reconstruction.\n"
                        "This may be helpful if the input cameras are already fully calibrated.",
            value=False,
        ),
        desc.FloatParam(
            name="maxAngleToPrior",
            label="Max Angle To Priors (deg.)",
            description="Maximum angle allowed regarding the input prior (in degrees) before refinement.",
            value=20.0,
            range=(0.0, 360.0, 1.0),
            advanced=True,
        ),
        desc.FloatParam(
            name="maxAngleToPriorRefined",
            label="Max Refined Angle To Priors (deg.)",
            description="Maximum angle allowed regarding the input prior (in degrees) after refinement.",
            value=2.0,
            range=(0.0, 360.0, 1.0),
            advanced=True,
        ),
        desc.FloatParam(
            name="maxAngularError",
            label="Max Angular Error (deg.)",
            description="Maximum angular error in global rotation averging (in degrees).",
            value=100.0,
            range=(0.0, 360.0, 1.0),
            advanced=True,
        ),
        desc.BoolParam(
            name="intermediateRefineWithFocal",
            label="Intermediate Refine: Focal",
            description="Intermediate refine with rotation and focal length only.",
            value=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="intermediateRefineWithFocalDist",
            label="Intermediate Refine: Focal And Distortion",
            description="Intermediate refine with rotation, focal length and distortion.",
            value=False,
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
            label="SfM File",
            description="Path to the output SfM file.",
            value=desc.Node.internalFolder + "panorama.abc",
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Views And Poses",
            description="Path to the output SfMData file with cameras (views and poses).",
            value=desc.Node.internalFolder + "cameras.sfm",
        ),
    ]
