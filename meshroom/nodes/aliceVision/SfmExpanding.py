__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class SfMExpanding(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmExpanding {allParams}'
    size = desc.DynamicNodeSize('input')

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Sparse Reconstruction'
    documentation = '''
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="SfMData file.",
            value="",
        ),
        desc.File(
            name="tracksFilename",
            label="Tracks File",
            description="Tracks file.",
            value="",
        ),
        desc.IntParam(
            name="localizerEstimatorMaxIterations",
            label="Localizer Max Ransac Iterations",
            description="Maximum number of iterations allowed in the Ransac step.",
            value=50000,
            range=(1, 100000, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="localizerEstimatorError",
            label="Localizer Max Ransac Error",
            description="Maximum error (in pixels) allowed for camera localization (resectioning).\n"
                        "If set to 0, it will select a threshold according to the localizer estimator used\n"
                        "(if ACRansac, it will analyze the input data to select the optimal value).",
            value=0.0,
            range=(0.0, 100.0, 0.1),
            advanced=True,
        ),
       desc.BoolParam(
            name="lockScenePreviouslyReconstructed",
            label="Lock Previously Reconstructed Scene",
            description="Lock previously reconstructed poses and intrinsics.\n"
                        "This option is useful for SfM augmentation.",
            value=False,
        ),
        desc.BoolParam(
            name="useLocalBA",
            label="Local Bundle Adjustment",
            description="It reduces the reconstruction time, especially for large datasets (500+ images),\n"
                        "by avoiding computation of the Bundle Adjustment on areas that are not changing.",
            value=True,
        ),
        desc.IntParam(
            name="localBAGraphDistance",
            label="LocalBA Graph Distance",
            description="Graph-distance limit to define the active region in the Local Bundle Adjustment strategy.",
            value=1,
            range=(2, 10, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="nbFirstUnstableCameras",
            label="First Unstable Cameras Nb",
            description="Number of cameras for which the bundle adjustment is performed every single time a camera is added.\n"
                        "This leads to more stable results while computations are not too expensive, as there is little data.\n"
                        "Past this number, the bundle adjustment will only be performed once for N added cameras.",
            value=30,
            range=(0, 100, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="maxImagesPerGroup",
            label="Max Images Per Group",
            description="Maximum number of cameras that can be added before the bundle adjustment has to be performed again.\n"
                        "This prevents adding too much data at once without performing the bundle adjustment.",
            value=30,
            range=(0, 100, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="bundleAdjustmentMaxOutliers",
            label="Max Nb Of Outliers After BA",
            description="Threshold for the maximum number of outliers allowed at the end of a bundle adjustment iteration.\n"
                        "Using a negative value for this threshold will disable BA iterations.",
            value=50,
            range=(-1, 1000, 1),
            advanced=True,
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
        desc.FloatParam(
            name="maxReprojectionError",
            label="Max Reprojection Error",
            description="Maximum reprojection error.",
            value=4.0,
            range=(0.1, 10.0, 0.1),
            advanced=True,
        ),
        desc.BoolParam(
            name="lockAllIntrinsics",
            label="Lock All Intrinsic Camera Parameters",
            description="Force to keep all the intrinsic parameters of the cameras (focal length, \n"
                        "principal point, distortion if any) constant during the reconstruction.\n"
                        "This may be helpful if the input cameras are already fully calibrated.",
            value=False,
        ),
        desc.IntParam(
            name="minNbCamerasToRefinePrincipalPoint",
            label="Min Nb Cameras To Refine Principal Point",
            description="Minimum number of cameras to refine the principal point of the cameras (one of the intrinsic parameters of the camera).\n"
                        "If we do not have enough cameras, the principal point is considered to be in the center of the image.\n"
                        "If minNbCamerasToRefinePrincipalPoint <= 0, the principal point is never refined."
                        "If minNbCamerasToRefinePrincipalPoint is set to 1, the principal point is always refined.",
            value=3,
            range=(0, 20, 1),
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
            value=desc.Node.internalFolder + "sfm.json",
        ),
    ]
