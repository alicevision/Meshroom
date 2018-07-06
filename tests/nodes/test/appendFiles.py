from meshroom.core import desc


class AppendFiles(desc.CommandLineNode):
    commandLine = 'cat {inputValue} {input2Value} {input3Value} {input4Value} > {outputValue}'

    inputs = [
        desc.File(
            name='input',
            label='Input File',
            description='''''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='input2',
            label='Input File 2',
            description='''''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='input3',
            label='Input File 3',
            description='''''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='input4',
            label='Input File 4',
            description='''''',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''''',
            value=desc.Node.internalFolder + 'appendText.txt',
            uid=[],
        )
    ]

