__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MeshResampling(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshResampling {allParams}'
    cpu = desc.Level.NORMAL
    ram = desc.Level.NORMAL

    category = 'Mesh Post-Processing'
    documentation = '''
This node allows to recompute the mesh surface with a new topology and uniform density.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input Mesh",
            description="Input mesh in the OBJ file format.",
            value="",
        ),
        desc.FloatParam(
            name="simplificationFactor",
            label="Simplification Factor",
            description="Simplification factor for the resampling.",
            value=0.5,
            range=(0.0, 1.0, 0.01),
        ),
        desc.IntParam(
            name="nbVertices",
            label="Fixed Number Of Vertices",
            description="Fixed number of output vertices.",
            value=0,
            range=(0, 1000000, 1),
        ),
        desc.IntParam(
            name="minVertices",
            label="Min Vertices",
            description="Minimum number of output vertices.",
            value=0,
            range=(0, 1000000, 1),
        ),
        desc.IntParam(
            name="maxVertices",
            label="Max Vertices",
            description="Maximum number of output vertices.",
            value=0,
            range=(0, 1000000, 1),
        ),
        desc.IntParam(
            name="nbLloydIter",
            label="Number Of Pre-Smoothing Iteration",
            description="Number of iterations for Lloyd pre-smoothing.",
            value=40,
            range=(0, 100, 1),
        ),
        desc.BoolParam(
            name="flipNormals",
            label="Flip Normals",
            description="Option to flip face normals.\n"
                        "It can be needed as it depends on the vertices order in triangles and the convention changes from one software to another.",
            value=False,
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
            label="Mesh",
            description="Output mesh in the OBJ file format.",
            value=desc.Node.internalFolder + "mesh.obj",
        ),
    ]
