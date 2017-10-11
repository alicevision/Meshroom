from meshroom.core import desc

class Meshing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'CMPMVS {mvsConfigValue} --meshing'

    mvsConfig = desc.FileAttribute(
            label='MVS Configuration file',
            description='',
            value='',
            shortName='',
            arg='',
            uid=[0],
            isOutput=False,
            )
