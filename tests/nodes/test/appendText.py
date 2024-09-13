from meshroom.core import desc


class AppendText(desc.CommandLineNode):
    commandLine = 'cat {inputValue} > {outputValue} && echo {inputTextValue} >> {outputValue}'

    inputs = [
        desc.File(
            name='input',
            label='Input File',
            description='''''',
            value='',
        ),
        desc.File(
            name='inputText',
            label='Input Text',
            description='''''',
            value='',
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''''',
            value=desc.Node.internalFolder + 'appendText.txt',
        ),
    ]
