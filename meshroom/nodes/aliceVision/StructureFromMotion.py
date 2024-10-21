__version__ = "3.3"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class StructureFromMotion(desc.AVCommandLineNode):
    commandLine = 'aliceVision_incrementalSfM {allParams}'
    size = desc.DynamicNodeSize('input')

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Sparse Reconstruction'
    documentation = '''
This node will analyze feature matches to understand the geometric relationship behind all the 2D observations,
and infer the rigid scene structure (3D points) with the pose (position and orientation) and internal calibration of all cameras.
The pipeline is a growing reconstruction process (called incremental SfM): it first computes an initial two-view reconstruction that is iteratively extended by adding new views.

1/ Fuse 2-View Matches into Tracks

It fuses all feature matches between image pairs into tracks. Each track represents a candidate point in space, visible from multiple cameras.
However, at this step of the pipeline, it still contains many outliers.

2/ Initial Image Pair

It chooses the best initial image pair. This choice is critical for the quality of the final reconstruction.
It should indeed provide robust matches and contain reliable geometric information.
So, this image pair should maximize the number of matches and the repartition of the corresponding features in each image.
But at the same time, the angle between the cameras should also be large enough to provide reliable geometric information.

3/ Initial 2-View Geometry

It computes the fundamental matrix between the 2 images selected and consider that the first one is the origin of the coordinate system.

4/ Triangulate

Now with the pose of the 2 first cameras, it triangulates the corresponding 2D features into 3D points.

5/ Next Best View Selection

After that, it selects all the images that have enough associations with the features that are already reconstructed in 3D.

6/ Estimate New Cameras

Based on these 2D-3D associations it performs the resectioning of each of these new cameras.
The resectioning is a Perspective-n-Point algorithm (PnP) in a RANSAC framework to find the pose of the camera that validates most of the features associations.
On each camera, a non-linear minimization is performed to refine the pose.

7/ Triangulate

From these new cameras poses, some tracks become visible by 2 or more resected cameras and it triangulates them.

8/ Optimize

It performs a Bundle Adjustment to refine everything: extrinsics and intrinsics parameters of all cameras as well as the position of all 3D points.
It filters the results of the Bundle Adjustment by removing all observations that have high reprojection error or insufficient angles between observations.

9/ Loop from 5 to 9

As we have triangulated new points, we get more image candidates for next best views selection and we can iterate from 5 to 9.
It iterates like that, adding cameras and triangulating new 2D features into 3D points and removing 3D points that became invalidated, until we cannot localize new views.

## Online
[https://alicevision.org/#photogrammetry/sfm](https://alicevision.org/#photogrammetry/sfm)
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
                description="",
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
                description="",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which the computed matches are stored.",
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
            exposed=True,
        ),
        desc.ChoiceParam(
            name="localizerEstimator",
            label="Localizer Estimator",
            description="Estimator type used to localize cameras (acransac, ransac, lsmeds, loransac, maxconsensus).",
            value="acransac",
            values=["acransac", "ransac", "lsmeds", "loransac", "maxconsensus"],
            advanced=True,
        ),
        desc.ChoiceParam(
            name="observationConstraint",
            label="Observation Constraint",
            description="Observation constraint mode used in the optimization:\n"
                        " - Basic: Use standard reprojection error in pixel coordinates.\n"
                        " - Scale: Use reprojection error in pixel coordinates but relative to the feature scale.",
            value="Scale",
            values=["Basic", "Scale"],
            advanced=True,
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
            name="minInputTrackLength",
            label="Min Input Track Length",
            description="Minimum track length in input of SfM.",
            value=2,
            range=(2, 10, 1),
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
        desc.FloatParam(
            name="minAngleInitialPair",
            label="Min Angle Initial Pair",
            description="Minimum angle for the initial pair.",
            value=5.0,
            range=(0.1, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="maxAngleInitialPair",
            label="Max Angle Initial Pair",
            description="Maximum angle for the initial pair.",
            value=40.0,
            range=(0.1, 60.0, 0.1),
            advanced=True,
        ),
        desc.BoolParam(
            name="useOnlyMatchesFromInputFolder",
            label="Use Only Matches From Input Folder",
            description="Use only matches from the input matchesFolder parameter.\n"
                        "Matches folders previously added to the SfMData file will be ignored.",
            value=False,
            invalidate=False,
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
        desc.BoolParam(
            name="mergeTracks",
            label="Merge Tracks",
            description="Enable/Disable the track merging. The merging between two tracks is made when they have duplicate features \n"
                        "coming from the same original feature (same describer type, same 2D position in the same view, same scale, \n"
                        "but different rotations and different feature id).\n",
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name="filterTrackForks",
            label="Filter Track Forks",
            description="Enable/Disable the track forks removal. A track contains a fork when incoherent matches \n"
                        "lead to multiple features in the same image for a single track.",
            value=False,
        ),
        desc.BoolParam(
            name="computeStructureColor",
            label="Compute Structure Color",
            description="Enable/Disable color computation of every 3D point.",
            value=True,
        ),
        desc.BoolParam(
            name="useAutoTransform",
            label="Automatic Alignment",
            description="Enable/Disable automatic alignment of the 3D reconstruction.\n"
                        "Determines scene orientation from the cameras' X axis,\n"
                        "determines north and scale from GPS information if available,\n"
                        "and defines ground level from the point cloud.",
            value=True,
        ),
        desc.File(
            name="initialPairA",
            label="Initial Pair A",
            description="View ID or filename of the first image (either with or without the full path).",
            value="",
        ),
        desc.File(
            name="initialPairB",
            label="Initial Pair B",
            description="View ID or filename of the second image (either with or without the full path).",
            value="",
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
        desc.BoolParam(
            name="logIntermediateSteps",
            label="Log Intermediate Steps",
            description="Dump the current state of the scene as an SfMData file every 3 resections.",
            value=False,
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
            description="Path to the output SfM point cloud file (in SfMData format).",
            value=desc.Node.internalFolder + "sfm.abc",
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Views And Poses",
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
