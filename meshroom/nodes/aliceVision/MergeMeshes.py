__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class MergeMeshes(desc.AVCommandLineNode):
    commandLine = 'aliceVision_mergeMeshes {allParams}'

    category = 'Utils'
    documentation = '''
This node allows to merge two meshes in one.

Operation types used to merge two meshes:

- boolean_union: Create a new mesh with the combined volume of the two input meshes.
- boolean_intersection: Create a new mesh from the intersected volumes of the two input meshes.
- boolean_difference: Create a new mesh from the volume of the first input mesh subtracted by the second input mesh.
'''

    inputs = [
        desc.File(
            name="inputFirstMesh",
            label="First Mesh",
            description="Input first mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).",
            value="",
        ),
        desc.File(
            name="inputSecondMesh",
            label="Second Mesh",
            description="Input second mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).",
            value="",
        ),
        desc.ChoiceParam(
            name="mergeOperation",
            label="Merge Operation",
            description="Operation types used to merge two meshes.",
            value="boolean_union",
            values=["boolean_union", "boolean_intersection", "boolean_difference"],
        ),
        desc.BoolParam(
            name="preProcess",
            label="Pre-Process",
            description="Pre-process the input meshes in order to avoid geometric errors in the merging process.",
            value=True,
        ),
        desc.BoolParam(
            name="postProcess",
            label="Post-Process",
            description="Post-process the output mesh in order to avoid future geometric errors.",
            value=True,
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
            description="Output mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).",
            value=desc.Node.internalFolder + "mesh.stl",
        ),
    ]
