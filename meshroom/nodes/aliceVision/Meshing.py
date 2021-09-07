__version__ = "7.0"

from meshroom.core import desc


class Meshing(desc.CommandLineNode):
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
            name='input',
            label='SfmData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name="depthMapsFolder",
            label='Depth Maps Folder',
            description='Input depth maps folder.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputMeshFileType',
            label='File Type',
            description='Output Mesh File Type',
            value='obj',
            values=('gltf', 'obj', 'fbx', 'stl'),
            exclusive=True,
            uid=[0],
            group='',
        ),
        desc.BoolParam(
            name='useBoundingBox',
            label='Custom Bounding Box',
            description='Edit the meshing bounding box. If enabled, it takes priority over the Estimate From SfM option. Parameters can be adjusted in advanced settings.',
            value=False,
            uid=[0],
            group=''
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
                            name="x", label="x", description="X Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z Offset",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01)
                        )
                    ],
                    joinChar=","
                ),
                desc.GroupAttribute(
                    name="bboxRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler degrees.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="Euler X Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-90.0, 90.0, 1)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Euler Y Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Euler Z Rotation",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1)
                        )
                    ],
                    joinChar=","
                ),
                desc.GroupAttribute(
                    name="bboxScale",
                    label="Scale",
                    description="Scale of the bounding box.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X Scale",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y Scale",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z Scale",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01)
                        )
                    ],
                    joinChar=","
                )
            ],
            joinChar=",",
            enabled=lambda node: node.useBoundingBox.value,
        ),
        desc.BoolParam(
            name='estimateSpaceFromSfM',
            label='Estimate Space From SfM',
            description='Estimate the 3d space from the SfM',
            value=True,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='estimateSpaceMinObservations',
            label='Min Observations For SfM Space Estimation',
            description='Minimum number of observations for SfM space estimation.',
            value=3,
            range=(0, 100, 1),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.estimateSpaceFromSfM.value,
        ),
        desc.FloatParam(
            name='estimateSpaceMinObservationAngle',
            label='Min Observations Angle For SfM Space Estimation',
            description='Minimum angle between two observations for SfM space estimation.',
            value=10,
            range=(0, 120, 1),
            uid=[0],
            enabled=lambda node: node.estimateSpaceFromSfM.value,
        ),
        desc.IntParam(
            name='maxInputPoints',
            label='Max Input Points',
            description='Max input points loaded from depth map images.',
            value=50000000,
            range=(500000, 500000000, 1000),
            uid=[0],
        ),
        desc.IntParam(
            name='maxPoints',
            label='Max Points',
            description='Max points at the end of the depth maps fusion.',
            value=5000000,
            range=(100000, 10000000, 1000),
            uid=[0],
        ),
        desc.IntParam(
            name='maxPointsPerVoxel',
            label='Max Points Per Voxel',
            description='Max points per voxel',
            value=1000000,
            range=(500000, 30000000, 1000),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='minStep',
            label='Min Step',
            description='The step used to load depth values from depth maps is computed from maxInputPts. '
            'Here we define the minimal value for this step, so on small datasets we will not spend '
            'too much time at the beginning loading all depth values.',
            value=2,
            range=(1, 20, 1),
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='partitioning',
            label='Partitioning',
            description='',
            value='singleBlock',
            values=('singleBlock', 'auto'),
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='repartition',
            label='Repartition',
            description='',
            value='multiResolution',
            values=('multiResolution', 'regularGrid'),
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='angleFactor',
            label='angleFactor',
            description='angleFactor',
            value=15.0,
            range=(0.0, 200.0, 1.0),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='simFactor',
            label='simFactor',
            description='simFactor',
            value=15.0,
            range=(0.0, 200.0, 1.0),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='pixSizeMarginInitCoef',
            label='pixSizeMarginInitCoef',
            description='pixSizeMarginInitCoef',
            value=2.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='pixSizeMarginFinalCoef',
            label='pixSizeMarginFinalCoef',
            description='pixSizeMarginFinalCoef',
            value=4.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='voteMarginFactor',
            label='voteMarginFactor',
            description='voteMarginFactor',
            value=4.0,
            range=(0.1, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='contributeMarginFactor',
            label='contributeMarginFactor',
            description='contributeMarginFactor',
            value=2.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='simGaussianSizeInit',
            label='simGaussianSizeInit',
            description='simGaussianSizeInit',
            value=10.0,
            range=(0.0, 50.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='simGaussianSize',
            label='simGaussianSize',
            description='simGaussianSize',
            value=10.0,
            range=(0.0, 50.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minAngleThreshold',
            label='minAngleThreshold',
            description='minAngleThreshold',
            value=1.0,
            range=(0.0, 10.0, 0.01),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='refineFuse',
            label='Refine Fuse',
            description='Refine depth map fusion with the new pixels size defined by angle and similarity scores.',
            value=True,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='helperPointsGridSize',
            label='Helper Points Grid Size',
            description='Grid Size for the helper points.',
            value=10,
            range=(0, 50, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='densify',
            label='Densify',
            description='Densify scene with helper points around vertices.',
            value=False,
            uid=[],
            advanced=True,
            group='',
        ),
        desc.IntParam(
            name='densifyNbFront',
            label='Densify: Front',
            description='Densify vertices: front.',
            value=1,
            range=(0, 5, 1),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.IntParam(
            name='densifyNbBack',
            label='Densify: Back',
            description='Densify vertices: back.',
            value=1,
            range=(0, 5, 1),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.FloatParam(
            name='densifyScale',
            label='Densify Scale',
            description='Scale between points used to densify the scene.',
            value=20.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.densify.value,
        ),
        desc.FloatParam(
            name='nPixelSizeBehind',
            label='Nb Pixel Size Behind',
            description='Number of pixel size units to vote behind the vertex as FULL status.',
            value=4.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='fullWeight',
            label='Full Weight',
            description='Weighting for full status.',
            value=1.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='voteFilteringForWeaklySupportedSurfaces',
            label='Weakly Supported Surface Support',
            description='Improve support of weakly supported surfaces with a tetrahedra fullness score filtering.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='addLandmarksToTheDensePointCloud',
            label='Add Landmarks To The Dense Point Cloud',
            description='Add SfM Landmarks to the dense point cloud.',
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='invertTetrahedronBasedOnNeighborsNbIterations',
            label='Tretrahedron Neighbors Coherency Nb Iterations',
            description='Invert cells status around surface to improve smoothness. Zero to disable.',
            value=10,
            range=(0, 30, 1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minSolidAngleRatio',
            label='minSolidAngleRatio',
            description='Change cells status on surface around vertices to improve smoothness using solid angle ratio between full/empty parts. Zero to disable.',
            value=0.2,
            range=(0.0, 0.5, 0.01),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='nbSolidAngleFilteringIterations',
            label='Nb Solid Angle Filtering Iterations',
            description='Filter cells status on surface around vertices to improve smoothness using solid angle ratio between full/empty parts. Zero to disable.',
            value=2,
            range=(0, 30, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='colorizeOutput',
            label='Colorize Output',
            description='Whether to colorize output dense point cloud and mesh.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='addMaskHelperPoints',
            label='Add Mask Helper Points',
            description='Add Helper points on the outline of the depth maps masks.',
            value=False,
            uid=[],
            advanced=True,
            group='',
        ),
        desc.FloatParam(
            name='maskHelperPointsWeight',
            label='Mask Helper Points Weight',
            description='Weight value for mask helper points. Zero means no helper point.',
            value=1.0,
            range=(0.0, 20.0, 1.0),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.addMaskHelperPoints.value,
        ),
        desc.IntParam(
            name='maskBorderSize',
            label='Mask Border Size',
            description='How many pixels on mask borders?',
            value=4,
            range=(0, 20, 1),
            uid=[0],
            advanced=True,
            enabled=lambda node: node.addMaskHelperPoints.value,
        ),
        desc.IntParam(
            name='maxNbConnectedHelperPoints',
            label='Helper Points: Max Segment Size',
            description='Maximum size of a segment of connected helper points before we remove it. Small segments of helper points can be on the real surface and should not be removed to avoid the creation of holes. 0 means that we remove all helper points. -1 means that we do not filter helper points at all.',
            value=50,
            range=(-1, 100, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='saveRawDensePointCloud',
            label='Save Raw Dense Point Cloud',
            description='Save dense point cloud before cut and filtering.',
            value=False,
            uid=[],
            advanced=True,
        ),
        desc.BoolParam(
            name='exportDebugTetrahedralization',
            label='Export DEBUG Tetrahedralization',
            description='Export debug cells score as tetrahedral mesh.\nWARNING: Could create HUGE meshes, only use on very small datasets.',
            value=False,
            uid=[],
            advanced=True,
        ),
        desc.IntParam(
            name='seed',
            label='Seed',
            description='Seed used for random operations. Zero means use of random device instead of a fixed seed.',
            value=0,
            range=(0, 10000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name="outputMesh",
            label="Mesh",
            description="Output mesh",
            value="{cache}/{nodeType}/{uid0}/mesh.{outputMeshFileTypeValue}",
            uid=[],
        ),
        desc.File(
            name="output",
            label="Dense SfMData",
            description="Output dense point cloud with visibilities (SfMData file format).",
            value="{cache}/{nodeType}/{uid0}/densePointCloud.abc",
            uid=[],
        ),
    ]
