from meshroom.core import desc


class AppendFiles(desc.CommandLineNode):
    commandLine = 'cat {inputValue} {input2Value} {input3Value} {input4Value} > {outputValue}'
    input = desc.File(
        label='Input File',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    input2 = desc.File(
        label='Input File 2',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    input3 = desc.File(
        label='Input File 3',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    input4 = desc.File(
        label='Input File 4',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    output = desc.File(
        label='Output',
        description='''''',
        value='{cache}/{nodeType}/{uid0}/appendText.txt',
        uid=[],
        isOutput=True,
        )
