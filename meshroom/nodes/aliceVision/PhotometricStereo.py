__version__ = "3.0"

from meshroom.core import desc

class PhotometricStereo(desc.CommandLineNode):
    commandLine = 'aliceVision_photometricStereo {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name='inputPath',
            label='SfmData',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='maskPath',
            label='Mask folder path',
            description='Mask folder path',
            value='',
            uid=[0],
        ),
        desc.File(
            name='pathToJSONLightFile',
            label='Lights Folder',
            description='Folder containing lighting information.',
            value='',
            uid=[0]
        )
    ]

    outputs = [
        desc.File(
            name='outputSfmData',
            label='SfmData',
            description='Path to the output folder',
            value=desc.Node.internalFolder + '/sfmData.sfm',
            uid=[],
            group='', # remove from command line
        ),
        desc.File(
            name='outputSfmDataAlbedo',
            label='SfmData Albedo',
            description='',
            value=desc.Node.internalFolder + '/albedoMaps.sfm',
            uid=[],
            group='', # remove from command line
        ),
        desc.File(
            name='outputSfmDataNormal',
            label='SfmData Normal',
            description='',
            value=desc.Node.internalFolder + '/normalMaps.sfm',
            uid=[],
            group='', # remove from command line
        ),
        desc.File(
            name='outputPath',
            label='Output Folder',
            description='Path to the output folder',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        # these attributes are only here to describe more accurately the output of the node
        # by specifying that it generates 2 sequences of images
        # (see in Viewer2D.qml how these attributes can be used)
        desc.File(
            name='normals',
            label='Normal Maps',
            description='Generated normal maps.',
            semantic='image',
            value=desc.Node.internalFolder + '<POSE_ID>_normals.png',
            uid=[],
            group='', # do not export on the command line
        ),
        desc.File(
            name='albedo',
            label='Albedo Maps',
            description='Generated albedo maps.',
            semantic='image',
            value=desc.Node.internalFolder + '<POSE_ID>_albedo.png',
            uid=[],
            group='', # do not export on the command line
        ),
    ]
