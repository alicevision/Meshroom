__version__ = "1.0"

from meshroom.core import desc

class SphereDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_sphereDetection {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.StringParam(
            name='input_model_path',
            label='Model file',
            description='Model file path',
            value='',
            uid=[],
        ),
        desc.StringParam(
            name='output_path',
            label='Output folder',
            description='Path to interal output folder',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='input_sfmdata_path',
            label='SFMData',
            description='Path to input SFMData',
            value='',
            uid=[0]
        ),
    ]
