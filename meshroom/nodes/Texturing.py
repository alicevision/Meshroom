from meshroom.core import desc

class Texturing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'CMPMVS {mvsConfigValue} --texturing'

    mvsConfig = desc.FileAttribute(
            label='MVS Configuration file',
            description='',
            value='',
            shortName='',
            arg='',
            uid=[0],
            isOutput=False,
            )
