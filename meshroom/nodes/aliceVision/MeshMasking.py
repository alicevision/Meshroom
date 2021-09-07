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
            label='Dense SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputMesh',
            label='Input Mesh',
            description='''Input Mesh''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputMeshFileType',
            label='Output File Type',
            description='File Type',
            value='obj',
            values=('obj', 'gltf', 'fbx', 'stl'),
            exclusive=True,
            uid=[0],
            group='',
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
            name='smoothBoundary',
            label='Smooth Boundary',
            description='Modify the triangles at the boundary to fit the masks.',
            value=False,
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
        desc.BoolParam(
            name='undistortMasks',
            label='Undistort Masks',
            description='''Undistort the masks with the same parameters as the matching image.
            Tick it if the masks are drawn on the original images.''',
            value=False,
            uid=[0]
        ),
        desc.BoolParam(
            name='usePointsVisibilities',
            label='Use points visibilities',
            description='''Use the points visibilities from the meshing to filter triangles.
            Example: when they are occluded, back-face, etc.''',
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
            description='''Output mesh.''',
            value=desc.Node.internalFolder + 'mesh.{outputMeshFileTypeValue}',
            uid=[],
        ),
    ]
