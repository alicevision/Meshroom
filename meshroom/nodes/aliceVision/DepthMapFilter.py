from meshroom.core import desc

class DepthMapFilter(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_depthMapFiltering {allParams}'
    gpu = desc.Level.NORMAL
    parallelization = desc.Parallelization(inputListParamName='viewpoints', blockSize=10)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            ),
    ]
