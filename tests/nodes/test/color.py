from meshroom.core import desc

class Color(desc.Node):

    inputs = [
        desc.GroupAttribute(
            name="rgb",
            label="rgb",
            description="rgb",
            exposed=True,
            groupDesc=[
                desc.FloatParam(name="r", label="r", description="r", value=0.0),
                desc.FloatParam(name="g", label="g", description="g", value=0.0),
                desc.FloatParam(name="b", label="b", description="b", value=0.0)                
            ]
        )
    ]

class NestedColor(desc.Node):

    inputs = [
        desc.GroupAttribute(
            name="rgb",
            label="rgb",
            description="rgb",
            exposed=True,
            groupDesc=[
                desc.FloatParam(name="r", label="r", description="r", value=0.0),
                desc.FloatParam(name="g", label="g", description="g", value=0.0),
                desc.FloatParam(name="b", label="b", description="b", value=0.0),
                desc.GroupAttribute(label="test", name="test", description="", 
                groupDesc=[
                    desc.FloatParam(name="r", label="r", description="r", value=0.0),
                    desc.FloatParam(name="g", label="g", description="g", value=0.0),
                    desc.FloatParam(name="b", label="b", description="b", value=0.0),
                    
                ])
            ]
        )
    ]