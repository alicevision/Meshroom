__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MeshDenoising(desc.AVCommandLineNode):
    commandLine = 'aliceVision_meshDenoising {allParams}'

    category = 'Mesh Post-Processing'
    documentation = '''
This experimental node allows to reduce noise from a Mesh.
for now, the parameters are difficult to control and vary a lot from one dataset to another.
'''

    inputs = [
        desc.File(
            name="input",
            label="Mesh",
            description="Input mesh in the OBJ file format.",
            value="",
        ),
        desc.IntParam(
            name="denoisingIterations",
            label="Denoising Iterations",
            description="Number of denoising iterations.",
            value=5,
            range=(0, 30, 1),
        ),
        desc.FloatParam(
            name="meshUpdateClosenessWeight",
            label="Mesh Update Closeness Weight",
            description="Closeness weight for mesh update. Must be positive.",
            value=0.001,
            range=(0.0, 0.1, 0.001),
        ),
        desc.FloatParam(
            name="lambda",
            label="Lambda",
            description="Regularization weight.",
            value=2.0,
            range=(0.0, 10.0, 0.01),
        ),
        desc.FloatParam(
            name="eta",
            label="Eta",
            description="Gaussian standard deviation for spatial weight, \n"
                        "scaled by the average distance between adjacent face centroids.\n"
                        "Must be positive.",
            value=1.5,
            range=(0.0, 20.0, 0.01),
        ),
        desc.FloatParam(
            name="mu",
            label="Mu",
            description="Gaussian standard deviation for guidance weight.",
            value=1.5,
            range=(0.0, 10.0, 0.01),
        ),
        desc.FloatParam(
            name="nu",
            label="Nu",
            description="Gaussian standard deviation for signal weight.",
            value=0.3,
            range=(0.0, 5.0, 0.01),
        ),
        desc.ChoiceParam(
            name="meshUpdateMethod",
            label="Mesh Update Method",
            description="Mesh ppdate method:\n"
                        " - ITERATIVE_UPDATE (default): ShapeUp styled iterative solver.\n"
                        " - POISSON_UPDATE: Poisson-based update from [Wang et al. 2015] 'Rolling guidance normal filter for geometric processing'.",
            value=0,
            values=[0, 1],
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
            label="Output",
            description="Output mesh in the OBJ file format.",
            value=desc.Node.internalFolder + "mesh.obj",
        ),
    ]
