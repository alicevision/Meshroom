from meshroom.core import desc

class DepthMapFilter(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_depthMapFiltering {allParams}'
    gpu = desc.Level.NORMAL

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            ),
    ]
