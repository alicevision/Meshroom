from meshroom.core import desc


class Ls(desc.CommandLineNode):
    commandLine = 'ls {inputValue} > {outputValue}'
    input = desc.File(
        label='Input',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    output = desc.File(
        label='Output',
        description='''''',
        value='{cache}/{nodeType}/{uid0}/ls.txt',
        uid=[],
        isOutput=True,
        )

