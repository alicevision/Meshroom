__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MeshFiltering(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshFiltering {allParams}'

    category = 'Dense Reconstruction'
    documentation = '''
This node applies a Laplacian filtering to remove local defects from the raw Meshing cut.
'''

    inputs = [
        desc.File(
            name="inputMesh",
            label="Mesh",
            description="Input mesh file.",
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
            name="keepLargestMeshOnly",
            label="Keep Only The Largest Mesh",
            description="Keep only the largest connected triangles group.",
            value=False,
        ),
        desc.ChoiceParam(
            name="smoothingSubset",
            label="Smoothing Subset",
            description="Subset for smoothing (all, surface_boundaries, surface_inner_part).",
            value="all",
            values=["all", "surface_boundaries", "surface_inner_part"],
            advanced=True,
        ),
        desc.IntParam(
            name="smoothingBoundariesNeighbours",
            label="Smoothing Boundaries Neighbours",
            description="Neighbours of the boundaries to consider.",
            value=0,
            range=(0, 20, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="smoothingIterations",
            label="Smoothing Iterations",
            description="Number of smoothing iterations.",
            value=5,
            range=(0, 50, 1),
        ),
        desc.FloatParam(
            name="smoothingLambda",
            label="Smoothing Lambda",
            description="Smoothing size.",
            value=1.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.ChoiceParam(
            name="filteringSubset",
            label="Filtering Subset",
            description="Subset for filtering (all, surface_boundaries, surface_inner_part).",
            value="all",
            values=["all", "surface_boundaries", "surface_inner_part"],
            advanced=True,
        ),
        desc.IntParam(
            name="filteringIterations",
            label="Filtering Iterations",
            description="Number of filtering iterations.",
            value=1,
            range=(0, 20, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="filterLargeTrianglesFactor",
            label="Filter Large Triangles Factor",
            description="Remove all large triangles.\n"
                        "We consider a triangle as large if one edge is bigger than N times the average edge length.\n"
                        "0 disables the filtering.",
            value=60.0,
            range=(0.0, 100.0, 0.1),
        ),
        desc.FloatParam(
            name="filterTrianglesRatio",
            label="Filter Triangles Ratio",
            description="Remove all triangles by ratio (largest edge /smallest edge).\n"
                        "0 disables the filtering.",
            value=0.0,
            range=(1.0, 50.0, 0.1),
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
            description="Output mesh file.",
            value=desc.Node.internalFolder + "mesh.{outputMeshFileTypeValue}",
        ),
    ]
