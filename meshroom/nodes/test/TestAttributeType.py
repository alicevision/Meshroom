""" Input node that creates custom attributes inheriting from existing ones.
"""
__version__ = "1.0"

# Meshroom
from meshroom.core import desc, custom

class TestAttributeType(desc.InputNode):
    documentation = """ Test node to access the frame that is currently selected in the gallery from a node. """
    category = 'Test/Bidule'

    # Inputs to the node
    inputs = [
        custom.JobParam(
            name="jobParam",
            label="Test Job Param",
            description="Random choice param with a hard-coded default list that will be updated dynamically\n"
                        "with a global update function defined at the attribute level.",
            value="a",
            values=["a", "b"],
            exclusive=True,
            uid=[0],
        )
    ]

    # Output which the node provides
    outputs = [
        desc.File(
            name="fullPath",
            label="Current Frame Full Path",
            description="Full path of the frame that is currently selected in the gallery.",
            value="",
            uid=[],
        ),
    ]

    def onJobParamChanged(self, node):
        print("On JobParamChanged")
        node.jobParam.update()