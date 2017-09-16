from processGraph import desc


class Ls(desc.CommandLineNode):
    commandLine = 'ls {inputValue} > {outputValue}'
    input = desc.FileAttribute(
        label='Input',
        uid=[0],
        )
    output = desc.FileAttribute(
        label='Output',
        value='{cache}/{nodeType}/{uid0}/ls.txt',
        isOutput=True,
        hasExpression=True,
        )

