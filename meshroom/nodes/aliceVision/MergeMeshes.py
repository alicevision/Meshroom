__version__ = "1.0"

from meshroom.core import desc


class MergeMeshes(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_mergeMeshes {allParams}'

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
            name='inputFirstMesh',
            label='Input First Mesh',
            description='Input First Mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputSecondMesh',
            label='Input Second Mesh',
            description='Input Second Mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='mergeOperation',
            label='Merge Operation',
            description='''Operation types used to merge two meshes.''',
            value='boolean_union',
            values=['boolean_union', 'boolean_intersection', 'boolean_difference'],
            exclusive=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='preProcess',
            label='Pre-Process',
            description='''Pre-process input meshes in order to avoid geometric errors in the merging process''',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='postProcess',
            label='Post-Process',
            description='''Post-process output mesh in order to avoid future geometric errors.''',
            value=True,
            uid=[0],
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
            name='output',
            label='Output mesh',
            description='''Output mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).''',
            value=desc.Node.internalFolder + 'mesh.stl',
            uid=[],
            ),
    ]
