from meshroom.core import desc

class DepthMap(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_depthMapEstimation {allParams}'
    gpu = desc.Level.INTENSIVE

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            ),
    ]

