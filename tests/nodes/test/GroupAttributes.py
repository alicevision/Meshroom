from meshroom.core import desc

class GroupAttributes(desc.Node):
    documentation = """ Test node to connect GroupAttributes to other GroupAttributes. """
    category = 'Test'

    # Inputs to the node
    inputs = [
        desc.GroupAttribute(
            name="firstGroup",
            label="First Group",
            description="Group at the root level.",
            group=None,
            exposed=True,
            groupDesc=[
                desc.IntParam(
                    name="firstGroupIntA",
                    label="Integer A",
                    description="First integer in group.",
                    value=1024,
                    range=(-1, 2000, 10),
                    exposed=True,
                ),
                desc.BoolParam(
                    name="firstGroupBool",
                    label="Boolean",
                    description="Boolean in group.",
                    value=True,
                    advanced=True,
                    exposed=True,
                ),
                desc.ChoiceParam(
                    name="firstGroupExclusiveChoiceParam",
                    label="Exclusive Choice Param",
                    description="Exclusive choice parameter.",
                    value="one",
                    values=["one", "two", "three", "four"],
                    exclusive=True,
                    exposed=True,
                ),
                desc.ChoiceParam(
                    name="firstGroupChoiceParam",
                    label="ChoiceParam",
                    description="Non-exclusive choice parameter.",
                    value=["one", "two"],
                    values=["one", "two", "three", "four"],
                    exclusive=False,
                    exposed=True
                ),
                desc.GroupAttribute(
                    name="nestedGroup",
                    label="Nested Group",
                    description="A group within a group.",
                    group=None,
                    exposed=True,
                    groupDesc=[
                        desc.FloatParam(
                            name="nestedGroupFloat",
                            label="Floating Number",
                            description="Floating number in group.",
                            value=1.0,
                            range=(0.0, 100.0, 0.01),
                            exposed=True
                        ),
                    ],
                ),
                desc.ListAttribute(
                    name="groupedList",
                    label="Grouped List",
                    description="List of groups within a group.",
                    advanced=True,
                    exposed=True,
                    elementDesc=desc.GroupAttribute(
                        name="listedGroup",
                        label="Listed Group",
                        description="Group in a list within a group.",
                        joinChar=":",
                        group=None,
                        groupDesc=[
                            desc.IntParam(
                                name="listedGroupInt",
                                label="Integer 1",
                                description="Integer in a group in a list within a group.",
                                value=12,
                                range=(3, 24, 1),
                                exposed=True,
                            ),
                        ],
                    ),
                ),
                desc.ListAttribute(
                    name="singleGroupedList",
                    label="Grouped List With Single Element",
                    description="List of integers within a group.",
                    advanced=True,
                    exposed=True,
                    elementDesc=desc.IntParam(
                        name="listedInt",
                        label="Integer In List",
                        description="Integer in a list within a group.",
                        value=40,
                    ),
                ),
            ],
        ),
        desc.IntParam(
            name="exposedInt",
            label="Exposed Integer",
            description="Integer at the rool level, exposed.",
            value=1000,
            exposed=True,
        ),
        desc.BoolParam(
            name="unexposedBool",
            label="Unexposed Boolean",
            description="Boolean at the root level, unexposed.",
            value=True,
        ),
        desc.GroupAttribute(
            name="inputGroup",
            label="Input Group",
            description="A group set as an input.",
            group=None,
            groupDesc=[
                desc.BoolParam(
                    name="inputBool",
                    label="Input Bool",
                    description="",
                    value=False,
                ),
            ],
        ),
    ]

    outputs = [
        desc.GroupAttribute(
            name="outputGroup",
            label="Output Group",
            description="A group set as an output.",
            group=None,
            exposed=True,
            groupDesc=[
                desc.BoolParam(
                    name="outputBool",
                    label="Output Bool",
                    description="",
                    value=False,
                    exposed=True,
                ),
            ],
        ),
    ]