from meshroom.core import desc

class NestedTest(desc.Node):

    inputs = [
        desc.GroupAttribute(
            name="xyz",
            label="xyz",
            description="xyz",
            exposed=True,
            groupDesc=[
                desc.FloatParam(name="x", label="x", description="x", value=0.0),
                desc.FloatParam(name="y", label="z", description="z", value=0.0),
                desc.FloatParam(name="z", label="z", description="z", value=0.0),
                desc.GroupAttribute(label="test", name="test", description="", 
                groupDesc=[
                    desc.StringParam(name="x", label="x", description="x", value="test"),
                    desc.FloatParam(name="y", label="z", description="z", value=0.0),
                    desc.FloatParam(name="z", label="z", description="z", value=0.0),                 
                ])
            ]
        )
    ]