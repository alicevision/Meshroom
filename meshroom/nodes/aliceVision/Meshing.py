from meshroom.core import desc

class Meshing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_meshing {allParams}'
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output mesh",
            description="Output mesh (OBJ file format).",
            value='{cache}/{nodeType}/{uid0}/mesh.obj',
            uid=[],
            ),
    ]
