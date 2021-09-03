__version__ = "1.0"

from meshroom.core import desc


class ConvertMesh(desc.CommandLineNode):
    commandLine = 'aliceVision_convertMesh {allParams}'

    category = 'Utils'
    documentation = '''This node allows to convert a mesh to another format.'''

    inputs = [
        desc.File(
            name='inputMesh',
            label='Input Mesh',
            description='Input Mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputMeshFileType',
            label='File Type',
            description='''Output Mesh Format (*.obj, *.gltf, *.fbx, *.stl).''',
            value='obj',
            values=('gltf', 'obj', 'fbx', 'stl'),
            exclusive=True,
            uid=[0],
            group='',
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
            label='Output Mesh',
            description='''Output mesh (*.obj, *.mesh, *.meshb, *.ply, *.off, *.stl).''',
            value=desc.Node.internalFolder + 'mesh.' + '{outputMeshFileTypeValue}',
            uid=[],
            ),
    ]
