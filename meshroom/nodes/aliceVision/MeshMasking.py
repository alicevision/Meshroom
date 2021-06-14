__version__ = "1.0"

from meshroom.core import desc


class MeshMasking(desc.CommandLineNode):
    commandLine = 'aliceVision_meshMasking {allParams}'
    category = 'Mesh Post-Processing'
    documentation = '''
Decimate triangles based on image masks.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputMesh',
            label='Input Mesh',
            description='''Input Mesh (OBJ file format).''',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="masksFolder",
                label="Masks Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="masksFolders",
            label="Masks Folders",
            description='Use masks from specific folder(s). Filename should be the same or the image uid.',
        ),
        desc.IntParam(
            name='threshold',
            label='Threshold',
            description='The minimum number of visibility to keep a vertex.',
            value=1,
            range=(1, 100, 1),
            uid=[0]
        ),
        desc.BoolParam(
            name='invert',
            label='Invert',
            description='''If ticked, the selected area is ignored.
            If not, only the selected area is considered.''',
            value=False,
            uid=[0]
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
            name='outputMesh',
            label='Output Mesh',
            description='''Output mesh (OBJ file format).''',
            value=desc.Node.internalFolder + 'mesh.obj',
            uid=[],
        ),
    ]
