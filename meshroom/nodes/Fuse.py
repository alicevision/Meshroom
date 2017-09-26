from meshroom.processGraph import desc

class Fuse(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'CMPMVS {mvsConfigValue} --fuse'

    mvsConfig = desc.FileAttribute(
            label='MVS Configuration file',
            description='',
            value='',
            shortName='',
            arg='',
            uid=[0],
            isOutput=False,
            )
