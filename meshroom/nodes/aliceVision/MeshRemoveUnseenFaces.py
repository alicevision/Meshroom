__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MeshRemoveUnseenFaces(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshRemoveUnseenFaces {allParams}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.NORMAL

    category = 'Dense Reconstruction'
    documentation = '''
Remove triangles from the mesh when the vertices are not visible by any camera.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="inputMesh",
            label="Mesh",
            description="Input Mesh file.",
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
        desc.IntParam(
            name="minObservations",
            label="Min Observations",
            description="Minimal number of observations to keep a vertex.",
            value=1,
            range=(0, 5, 1),
        ),
        desc.IntParam(
            name="minVertices",
            label="Min Vertices to Remove a Triangle",
            description="Minimal number of killed vertices in a triangle to remove the triangle.",
            value=3,
            range=(1, 3, 1),
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
