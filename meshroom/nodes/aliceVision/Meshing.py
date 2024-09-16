__version__ = "7.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class Meshing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshing {allParams}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Dense Reconstruction'
    documentation = '''
This node creates a dense geometric surface representation of the scene.

First, it fuses all the depth maps into a global dense point cloud with an adaptive resolution.
It then performs a 3D Delaunay tetrahedralization and a voting procedure is done to compute weights on cells and weights on facets connecting the cells.
A Graph Cut Max-Flow is applied to optimally cut the volume. This cut represents the extracted mesh surface.

## Online
[https://alicevision.org/#photogrammetry/meshing](https://alicevision.org/#photogrammetry/meshing)
'''

    inputs = [
        desc.File(
            name="input",
            label="SfmData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="depthMapsFolder",
            label="Depth Maps Folder",
            description="Input depth maps folder.",
            value="",
        ),
        desc.ChoiceParam(
            name="outputMeshFileType",
            label="Mesh Type",
            description="File type for the output mesh.",
            value="obj",
            values=["gltf", "obj", "fbx", "stl"],
            group="",
        ),
        desc.BoolParam(
            name="useBoundingBox",
            label="Custom Bounding Box",
            description="Edit the meshing bounding box.\n"
                        "If enabled, it takes priority over the 'Estimate Space From SfM' option.\n"
                        "Parameters can be adjusted in advanced settings.",
            value=False,
            group="",
        ),
        desc.GroupAttribute(
            name="boundingBox",
            label="Bounding Box Settings",
            description="Translation, rotation and scale of the bounding box.",
            groupDesc=[
                desc.GroupAttribute(
                    name="bboxTranslation",
                    label="Translation",
                    description="Position in space.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z offset.",
                            value=0.0,
                            range=(-20.0, 20.0, 0.01),
                        ),
                    ],
                    joinChar=",",
                ),
                desc.GroupAttribute(
                    name="bboxRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler degrees.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="Euler X rotation.",
                            value=0.0,
                            range=(-90.0, 90.0, 1.0)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Euler Y rotation.",
                            value=0.0,
                            range=(-180.0, 180.0, 1.0)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Euler Z rotation.",
                            value=0.0,
                            range=(-180.0, 180.0, 1.0)
                        ),
                    ],
                    joinChar=",",
                ),
                desc.GroupAttribute(
                    name="bboxScale",
                    label="Scale",
                    description="Scale of the bounding box.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X scale.",
                            value=1.0,
                            range=(0.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y scale.",
                            value=1.0,
                            range=(0.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z scale.",
                            value=1.0,
                            range=(0.0, 20.0, 0.01),
                        ),
                    ],
                    joinChar=",",
                ),
            ],
            joinChar=",",
            enabled=lambda node: node.useBoundingBox.value,
        ),
        desc.BoolParam(
            name="estimateSpaceFromSfM",
            label="Estimate Space From SfM",
            description="Estimate the 3D space from the SfM.",
            value=True,
            advanced=True,
        ),
        desc.IntParam(
            name="estimateSpaceMinObservations",
            label="Min Observations For SfM Space Estimation",
            description="Minimum number of observations for the space estimation from the SfM.",
            value=3,
            range=(0, 100, 1),
            advanced=True,
            enabled=lambda node: node.estimateSpaceFromSfM.value,
        ),
        desc.FloatParam(
            name="estimateSpaceMinObservationAngle",
            label="Min Observations Angle For SfM Space Estimation",
            description="Minimum angle between two observations for the space estimation from the SfM.",
            value=10.0,
            range=(0.0, 120.0, 1.0),
            enabled=lambda node: node.estimateSpaceFromSfM.value,
        ),
        desc.IntParam(
            name="maxInputPoints",
            label="Max Input Points",
            description="Maximum input points loaded from depth map images.",
            value=50000000,
            range=(500000, 500000000, 1000),
        ),
        desc.IntParam(
            name="maxPoints",
            label="Max Points",
            description="Maximum points at the end of the depth maps fusion.",
            value=5000000,
            range=(100000, 10000000, 1000),
        ),
        desc.IntParam(
            name="maxPointsPerVoxel",
            label="Max Points Per Voxel",
            description="Maximum points per voxel.",
            value=1000000,
            range=(500000, 30000000, 1000),
            advanced=True,
        ),
        desc.IntParam(
            name="minStep",
            label="Min Step",
            description="The step used to load depth values from depth maps is computed from 'maxInputPoints'.\n"
                        "Here we define the minimum value for this step, so on small datasets we will not spend "
                        "too much time at the beginning loading all the depth values.",
            value=2,
            range=(1, 20, 1),
            advanced=True,
        ),
        desc.ChoiceParam(
            name="partitioning",
            label="Partitioning",
            description="Single block or auto partitioning.",
            value="singleBlock",
            values=["singleBlock", "auto"],
            advanced=True,
        ),
        desc.ChoiceParam(
            name="repartition",
            label="Repartition",
            description="Multi-resolution or regular grid-based repartition.",
            value="multiResolution",
            values=["multiResolution", "regularGrid"],
            advanced=True,
        ),
        desc.FloatParam(
            name="angleFactor",
            label="Angle Factor",
            description="Angle factor.",
            value=15.0,
            range=(0.0, 200.0, 1.0),
            advanced=True,
        ),
        desc.FloatParam(
            name="simFactor",
            label="Sim Factor",
            description="Sim factor.",
            value=15.0,
            range=(0.0, 200.0, 1.0),
            advanced=True,
        ),
        desc.IntParam(
            name="minVis",
            label="Min Observations",
            description="Filter points based on their number of observations.",
            value=2,
            range=(1, 20, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="pixSizeMarginInitCoef",
            label="Pix Size Margin Init Coef",
            description="Size of the margin init coefficient, in pixels.",
            value=2.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="pixSizeMarginFinalCoef",
            label="Pix Size Margin Final Coef",
            description="Size of the margin final coefficient, in pixels.",
            value=4.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="voteMarginFactor",
            label="Vote Margin Factor",
            description="Vote margin factor.",
            value=4.0,
            range=(0.1, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="contributeMarginFactor",
            label="Contribute Margin Factor",
            description="Contribute margin factor.",
            value=2.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="simGaussianSizeInit",
            label="Sim Gaussian Size Init",
            description="Sim Gaussian size init.",
            value=10.0,
            range=(0.0, 50.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="simGaussianSize",
            label="Sim Gaussian Size",
            description="Sim Gaussian size.",
            value=10.0,
            range=(0.0, 50.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="minAngleThreshold",
            label="Min Angle Threshold",
            description="Minimum angle threshold.",
            value=1.0,
            range=(0.0, 10.0, 0.01),
            advanced=True,
        ),
        desc.BoolParam(
            name="refineFuse",
            label="Refine Fuse",
            description="Refine depth map fusion with the new pixels size defined by angle and similarity scores.",
            value=True,
            advanced=True,
        ),
        desc.IntParam(
            name="helperPointsGridSize",
            label="Helper Points Grid Size",
            description="Grid size for the helper points.",
            value=10,
            range=(0, 50, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="densify",
            label="Densify",
            description="Densify scene with helper points around vertices.",
            value=False,
            invalidate=False,
            advanced=True,
            group="",
        ),
        desc.IntParam(
            name="densifyNbFront",
            label="Densify: Front",
            description="Densify vertices: front.",
            value=1,
            range=(0, 5, 1),
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.IntParam(
            name="densifyNbBack",
            label="Densify: Back",
            description="Densify vertices: back.",
            value=1,
            range=(0, 5, 1),
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.FloatParam(
            name="densifyScale",
            label="Densify Scale",
            description="Scale between points used to densify the scene.",
            value=20.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.FloatParam(
            name="nPixelSizeBehind",
            label="Nb Pixel Size Behind",
            description="Number of pixel size units to vote behind the vertex as FULL status.",
            value=4.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="fullWeight",
            label="Full Weight",
            description="Weighting for full status.",
            value=1.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.BoolParam(
            name="voteFilteringForWeaklySupportedSurfaces",
            label="Weakly Supported Surface Support",
            description="Improve support of weakly supported surfaces with a tetrahedra fullness score filtering.",
            value=True,
        ),
        desc.BoolParam(
            name="addLandmarksToTheDensePointCloud",
            label="Add Landmarks To The Dense Point Cloud",
            description="Add SfM landmarks to the dense point cloud.",
            value=False,
            advanced=True,
        ),
        desc.IntParam(
            name="invertTetrahedronBasedOnNeighborsNbIterations",
            label="Tretrahedron Neighbors Coherency Nb Iterations",
            description="Invert cells status around surface to improve smoothness.\n"
                        "Set to 0 to disable.",
            value=10,
            range=(0, 30, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="minSolidAngleRatio",
            label="Min Solid Angle Ratio",
            description="Change cells status on surface around vertices to improve smoothness using solid angle \n"
                        "ratio between full/empty parts. Set to 0 to disable.",
            value=0.2,
            range=(0.0, 0.5, 0.01),
            advanced=True,
        ),
        desc.IntParam(
            name="nbSolidAngleFilteringIterations",
            label="Nb Solid Angle Filtering Iterations",
            description="Filter cells status on surface around vertices to improve smoothness using solid angle ratio \n"
                        "between full/empty parts. Set to 0 to disable.",
            value=2,
            range=(0, 30, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="colorizeOutput",
            label="Colorize Output",
            description="Whether to colorize output dense point cloud and mesh.",
            value=False,
        ),
        desc.BoolParam(
            name="addMaskHelperPoints",
            label="Add Mask Helper Points",
            description="Add Helper points on the outline of the depth maps masks.",
            value=False,
            invalidate=False,
            advanced=True,
            group="",
        ),
        desc.FloatParam(
            name="maskHelperPointsWeight",
            label="Mask Helper Points Weight",
            description="Weight value for mask helper points. 0 means no helper point.",
            value=1.0,
            range=(0.0, 20.0, 1.0),
            advanced=True,
            enabled=lambda node: node.addMaskHelperPoints.value,
        ),
        desc.IntParam(
            name="maskBorderSize",
            label="Mask Border Size",
            description="Number of pixels on mask borders.",
            value=4,
            range=(0, 20, 1),
            advanced=True,
            enabled=lambda node: node.addMaskHelperPoints.value,
        ),
        desc.IntParam(
            name="maxNbConnectedHelperPoints",
            label="Helper Points: Max Segment Size",
            description="Maximum size of a segment of connected helper points before we remove it.\n"
                        "Small segments of helper points can be on the real surface and should not be removed to avoid the creation of holes.\n"
                        "0 means that all helper points are removed. -1 means that helper points are not filtered at all.",
            value=50,
            range=(-1, 100, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="saveRawDensePointCloud",
            label="Save Raw Dense Point Cloud",
            description="Save dense point cloud before cut and filtering.",
            value=False,
            invalidate=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="exportDebugTetrahedralization",
            label="Export Debug Tetrahedralization",
            description="Export debug cells score as tetrahedral mesh.\n"
                        "WARNING: Could create HUGE meshes, only use on very small datasets.",
            value=False,
            invalidate=False,
            advanced=True,
        ),
        desc.IntParam(
            name="seed",
            label="Seed",
            description="Seed used for random operations.\n"
                        "0 means use of random device instead of a fixed seed.",
            value=0,
            range=(0, 10000, 1),
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
            name="outputMesh",
            label="Mesh",
            description="Output mesh.",
            value=desc.Node.internalFolder + "mesh.{outputMeshFileTypeValue}",
        ),
        desc.File(
            name="output",
            label="Dense SfMData",
            description="Output dense point cloud with visibilities (SfMData file format).",
            value=desc.Node.internalFolder + "densePointCloud.abc",
        ),
    ]
