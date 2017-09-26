from meshroom.processGraph import desc

class DepthMap(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'CMPMVS {mvsConfigValue} --createDepthmap'

    mvsConfig = desc.FileAttribute(
            label='MVS Configuration file',
            description='',
            value='',
            shortName='',
            arg='',
            uid=[0],
            isOutput=False,
            )
