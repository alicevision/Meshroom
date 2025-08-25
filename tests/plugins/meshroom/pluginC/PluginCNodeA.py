__version__ = "1.0"
__license__ = "no-license"

from meshroom.core import desc


class PluginCNodeA(desc.Node):
    """PluginCNodeA"""
    
    author = "testAuthor"
    
    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="",
            value="",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="",
        ),
    ]
