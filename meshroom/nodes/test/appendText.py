from meshroom.core import desc


class AppendText(desc.CommandLineNode):
    commandLine = 'cat {inputValue} > {outputValue} && echo {inputTextValue} >> {outputValue}'
    input = desc.FileAttribute(
        label='Input File',
        uid=[0],
        )
    output = desc.FileAttribute(
        label='Output',
        value='{cache}/{nodeType}/{uid0}/appendText.txt',
        isOutput=True,
        hasExpression=True,
        )
    inputText = desc.FileAttribute(
        label='Input Text',
        uid=[0],
        )

