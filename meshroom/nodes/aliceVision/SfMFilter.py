__version__ = "1.0"

from meshroom.core import desc
import os.path


class SfMFilter(desc.AVCommandLineNode):
    commandLine = 'aliceVision_filterSfM {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
This node allows to filter the SfM data.

It filters the landmarks having:
- an insufficient number of observations
- a large pixel size compared to their neighbors.

It also filters the landmark observations to allow only a limited number 
of observations per landmark; the nearest observations are kept.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.GroupAttribute(
            name="filterParams",
            label="Filter Parameters",
            description="Filter Parameters.",
            joinChar=":",
            groupDesc=[
                desc.GroupAttribute(
                    name="filterLandmarks",
                    label="Filter Landmarks",
                    description="Filter Landmarks over multiple steps",
                    joinChar=":",
                    groupDesc=[
                        desc.BoolParam(
                            name="filterLandmarksEnabled",
                            label="Enable",
                            description="Enable Landmarks Filtering.",
                            value=True,
                            uid=[0],
                        ),
                        desc.GroupAttribute(
                            name="step1",
                            label="Step 1",
                            description="Remove landmarks with insufficient observations",
                            joinChar=":",
                            enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value,
                            groupDesc=[
                                desc.BoolParam(
                                    name="step1Enabled",
                                    label="Enable",
                                    description="Enable Step 1.",
                                    value=True,
                                    uid=[0],
                                ),
                                desc.IntParam(
                                    name="minNbObservationsPerLandmark",
                                    label="Minimum Nb of Observations",
                                    description="Minimum number of observations required to keep a landmark.",
                                    value=3,
                                    range=(0, 20, 1),
                                    enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value
                                        and node.filterParams.filterLandmarks.step1.step1Enabled.value,
                                    uid=[0],
                                )
                            ]
                        ),
                        desc.GroupAttribute(
                            name="step2",
                            label="Step 2",
                            description="Remove landmarks with dissimilar observations of 3D landmark neighbors",
                            joinChar=":",
                            enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value,
                            groupDesc=[
                                desc.BoolParam(
                                    name="step2Enabled",
                                    label="Enable",
                                    description="Enable Step 2.",
                                    value=True,
                                    uid=[0],
                                ),
                                desc.FloatParam(
                                    name="minScore",
                                    label="Minimum Similarity Score",
                                    description="Minimum similarity score between the observations of the landmark and of its neighbors.",
                                    value=0.3,
                                    range=(0., 1., .1),
                                    enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value
                                        and node.filterParams.filterLandmarks.step2.step2Enabled.value,
                                    uid=[0],
                                ),
                                desc.IntParam(
                                    name="nbNeighbors3D",
                                    label="Nb of Neighbors in 3D",
                                    description="Number of neighbor landmarks used in making the decision for best observations.",
                                    value=10,
                                    range=(1, 50, 1),
                                    enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value
                                        and node.filterParams.filterLandmarks.step2.step2Enabled.value,
                                    uid=[0],
                                )
                            ]
                        ),
                        desc.GroupAttribute(
                            name="step3",
                            label="Step 3",
                            description="Remove landmarks with worse resolution than neighbors",
                            joinChar=":",
                            enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value,
                            groupDesc=[
                                desc.BoolParam(
                                    name="step3Enabled",
                                    label="Enable",
                                    description="Enable Step 3.",
                                    value=True,
                                    uid=[0],
                                ),
                                desc.FloatParam(
                                    name="radiusScale",
                                    label="Radius Scale",
                                    description="Scale factor applied to pixel size based radius filter applied to landmarks.",
                                    value=2.,
                                    range=(0., 20., 1.),
                                    enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value
                                        and node.filterParams.filterLandmarks.step3.step3Enabled.value,
                                    uid=[0],
                                ),
                                desc.BoolParam(
                                    name="useFeatureScale",
                                    label="Use Feature Scale",
                                    description="If true, use feature scale for computing pixel size. Otherwise, use a scale of 1 pixel.",
                                    value=True,
                                    enabled=lambda node: node.filterParams.filterLandmarks.filterLandmarksEnabled.value
                                        and node.filterParams.filterLandmarks.step3.step3Enabled.value,
                                    uid=[0],
                                )
                            ]
                        )
                    ]
                ),
                desc.GroupAttribute(
                    name="filterObservations3D",
                    label="Filter Observations 3D",
                    description="Select best observations for observation consistency between 3D neighboring landmarks",
                    joinChar=":",
                    groupDesc=[
                        desc.BoolParam(
                            name="filterObservations3DEnabled",
                            label="Enable",
                            description="Enable Observations Filtering in 3D.",
                            value=True,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="maxNbObservationsPerLandmark",
                            label="Maximum Nb of Observations",
                            description="Maximum number of allowed observations per landmark.",
                            value=2,
                            range=(0, 20, 1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value,
                            uid=[0],
                        ),
                        desc.BoolParam(
                            name="propagationEnabled",
                            label="Enable Neighbors Influence",
                            description="Enable propagating neighbors' info (scores, observations) iteratively.",
                            value=True,
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="nbNeighbors3D",
                            label="Nb of Neighbors in 3D",
                            description="Number of neighbor landmarks used in making the decision for best observations.",
                            value=10,
                            range=(1, 50, 1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value,
                            uid=[0],
                        ),
                        desc.BoolParam(
                            name="observationsPropagationEnabled",
                            label="Enable Observations Propagation",
                            description="Enable propagating neighbors observations before propagating the scores.",
                            value=True,
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="observationsPropagationFrequency",
                            label="Frequency of Observations Propagation",
                            description="Specifies every how many iterations should the observations be propagated.",
                            value=1,
                            range=(0, 10, 1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value
                                and node.filterParams.filterObservations3D.observationsPropagationEnabled.value,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="observationsPropagationCount",
                            label="Count of Observations Propagation",
                            description="Maximum number of times the observations are propagated (0 for no limit).",
                            value=1,
                            range=(0, 10, 1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value
                                and node.filterParams.filterObservations3D.observationsPropagationEnabled.value,
                            uid=[0],
                        ),
                        desc.BoolParam(
                            name="observationsPropagationKeep",
                            label="Keep Propagated Observations",
                            description="Specifies if propagated observations are to be kept at the end.",
                            value=False,
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value
                                and node.filterParams.filterObservations3D.observationsPropagationEnabled.value,
                            uid=[0],
                        ),
                        desc.FloatParam(
                            name="neighborsInfluence",
                            label="Neighbors Influence",
                            description="Specifies how much influential the neighbors are in selecting the best observations. "
                                "Between 0. and 1., the closer to 1., the more influencial the neighborhood is.",
                            value=.5,
                            range=(0., 1., .1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="nbIterations",
                            label="Nb of Iterations",
                            description="Number of iterations to propagate neighbors information.",
                            value=5,
                            range=(1, 100, 1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value,
                            uid=[0],
                        ),
                        desc.BoolParam(
                            name="dampingEnabled",
                            label="Enable damping",
                            description="Enable additional damping of observations to reject after each iterations.",
                            value=True,
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value,
                            uid=[0],
                        ),
                        desc.FloatParam(
                            name="dampingFactor",
                            label="Damping Factor",
                            description="Multiplicative damping factor.",
                            value=.5,
                            range=(0., 1., .1),
                            enabled=lambda node: node.filterParams.filterObservations3D.filterObservations3DEnabled.value
                                and node.filterParams.filterObservations3D.propagationEnabled.value
                                and node.filterParams.filterObservations3D.dampingEnabled.value,
                            uid=[0],
                        )
                    ]
                ),
                desc.GroupAttribute(
                    name="filterObservations2D",
                    label="Filter Observations 2D",
                    description="Select best observations for observation consistency between 2D projected neighboring "
                        "landmarks per view.\nEventually remove landmarks with no remaining observations.\n"
                        "Also estimate depth map mask radius per view based on landmarks.",
                    joinChar=":",
                    groupDesc=[
                        desc.BoolParam(
                            name="filterObservations2DEnabled",
                            label="Enable",
                            description="Enable Observations Filtering in 2D.",
                            value=True,
                            uid=[0],
                        ),
                        desc.IntParam(
                            name="nbNeighbors2D",
                            label="Nb of Neighbors in 2D",
                            description="Number of neighbor observations to be considered for the landmarks-based masking.",
                            value=5,
                            range=(1, 50, 1),
                            enabled=lambda node: node.filterParams.filterObservations2D.filterObservations2DEnabled.value,
                            uid=[0],
                        ),
                        desc.FloatParam(
                            name="percentile",
                            label="Percentile",
                            description="Used as a quantile probability for filtering relatively outlier observations.",
                            value=.95,
                            range=(0., 1., .01),
                            enabled=lambda node: node.filterParams.filterObservations2D.filterObservations2DEnabled.value,
                            uid=[0],
                        ),
                        desc.FloatParam(
                            name="maskRadiusThreshold",
                            label="Mask Radius Threshold",
                            description="Percentage of image size to be used as an upper limit for estimated mask radius.",
                            value=.1,
                            range=(0., 1., .1),
                            enabled=lambda node: node.filterParams.filterObservations2D.filterObservations2DEnabled.value,
                            uid=[0],
                        )
                    ]
                )
            ]
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="",
                value="",
                uid=[], #TODO
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors."
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="",
                value="",
                uid=[], #TODO
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which the computed matches are stored."
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            value=["dspsift"],
            values=["sift", "sift_float", "sift_upright", "dspsift", "akaze", "akaze_liop", "akaze_mldb", "cctag3", "cctag4", "sift_ocv", "akaze_ocv", "tag16h5"],
            exclusive=False,
            uid=[],  # TODO: 0
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output SfMData file.",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "sfmData") + ".abc",
            uid=[],
        ),
        desc.File(
            name="outputRadiiFile",
            label="Output Radii File",
            description="Output Radii file containing the estimated projection radius of observations per view.",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "radii") + ".txt",
            uid=[],
        ),
    ]
