from meshroom.core import desc


class AppendText(desc.CommandLineNode):
    commandLine = 'cat {inputValue} > {outputValue} && echo {inputTextValue} >> {outputValue}'
    input = desc.File(
        label='Input File',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )
    output = desc.File(
        label='Output',
        description='''''',
        value='{cache}/{nodeType}/{uid0}/appendText.txt',
        uid=None,
        isOutput=True,
        )
    inputText = desc.File(
        label='Input Text',
        description='''''',
        value='',
        uid=[0],
        isOutput=False,
        )

