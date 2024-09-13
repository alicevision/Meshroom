from meshroom.core import desc


class Ls(desc.CommandLineNode):
    commandLine = 'ls {inputValue} > {outputValue}'
    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''''',
            value='',
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''''',
            value=desc.Node.internalFolder + 'ls.txt',
        )
    ]
