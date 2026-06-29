from meshroom.core import desc
from meshroom.core.desc import Level


class AllAttributesNode(desc.Node):
    """
    Reference node showcasing every available Meshroom attribute type.
    Both in inputs and outputs.
    Useful as a development reference or a template.
    """

    cpu = Level.NORMAL
    ram = Level.NORMAL
    gpu = Level.NONE

    inputs = [

        # -----------------------------------------------------------------------
        # Basic Parameters
        # -----------------------------------------------------------------------
        desc.BoolParam(
            name="boolParam",
            label="Boolean",
            description="A simple boolean toggle.",
            value=False,
        ),
        desc.IntParam(
            name="intParam",
            label="Integer",
            description="An integer with a range constraint.",
            value=10,
            range=(0, 100, 1),
        ),
        desc.FloatParam(
            name="floatParam",
            label="Float",
            description="A floating-point value with a range constraint.",
            value=3.14,
            range=(0.0, 10.0, 0.01),
        ),
        desc.StringParam(
            name="stringParam",
            label="String",
            description="A free-form string.",
            value="default",
        ),
        desc.File(
            name="fileParam",
            label="File",
            description="A file or directory path.",
            value="",
        ),
        desc.ChoiceParam(
            name="exclusiveChoice",
            label="Exclusive Choice",
            description="A single-selection dropdown.",
            value="optionA",
            values=["optionA", "optionB", "optionC"],
            exclusive=True,
        ),
        desc.ChoiceParam(
            name="multiChoice",
            label="Multi Choice",
            description="A multiple-selection list.",
            value=["optionA"],
            values=["optionA", "optionB", "optionC"],
            exclusive=False,
        ),
        desc.PushButtonParam(
            name="buttonParam",
            label="Action Button",
            description="A UI-only action button. No stored value.",
        ),

        # -----------------------------------------------------------------------
        # Advanced Parameters (hidden by default in UI)
        # -----------------------------------------------------------------------
        desc.IntParam(
            name="advancedInt",
            label="Advanced Integer",
            description="An advanced parameter hidden by default.",
            value=42,
            range=(0, 1000, 1),
            advanced=True,
        ),
        desc.FloatParam(
            name="advancedFloat",
            label="Advanced Float",
            description="An advanced float hidden by default.",
            value=0.5,
            range=(0.0, 1.0, 0.01),
            advanced=True,
        ),

        # -----------------------------------------------------------------------
        # Enabled conditionally (dynamic enable via lambda)
        # -----------------------------------------------------------------------
        desc.FloatParam(
            name="conditionalParam",
            label="Conditional Float",
            description="Only active when boolParam is True.",
            value=1.0,
            range=(0.0, 10.0, 0.1),
            enabled=lambda node: node.boolParam.value,
        ),

        # -----------------------------------------------------------------------
        # Compound Containers
        # -----------------------------------------------------------------------
        desc.ListAttribute(
            name="fileList",
            label="File List",
            description="A homogeneous list of file paths.",
            elementDesc=desc.File(
                name="file",
                label="File",
                description="A single file entry.",
                value="",
            ),
            joinChar=" ",
        ),
        desc.ListAttribute(
            name="intList",
            label="Integer List",
            description="A homogeneous list of integers.",
            elementDesc=desc.IntParam(
                name="item",
                label="Item",
                description="",
                value=0,
                range=(0, 1000, 1),
            ),
            joinChar=",",
        ),
        desc.GroupAttribute(
            name="paramGroup",
            label="Parameter Group",
            description="A fixed collection of heterogeneous attributes.",
            items=[
                desc.BoolParam(
                    name="groupBool",
                    label="Group Bool",
                    description="",
                    value=True,
                ),
                desc.IntParam(
                    name="groupInt",
                    label="Group Int",
                    description="",
                    value=5,
                    range=(0, 50, 1),
                ),
                desc.FloatParam(
                    name="groupFloat",
                    label="Group Float",
                    description="",
                    value=0.1,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.StringParam(
                    name="groupString",
                    label="Group String",
                    description="",
                    value="group_default",
                ),
                desc.File(
                    name="groupFile",
                    label="Group File",
                    description="",
                    value="",
                ),
            ],
        ),

        # -----------------------------------------------------------------------
        # Geometry Helpers
        # -----------------------------------------------------------------------
        desc.Size2d(
            name="size2d",
            label="Size 2D",
            description="A 2D size (width x height).",
            width=1920.0,
            height=1080.0,
        ),
        desc.Vec2d(
            name="vec2d",
            label="Vector 2D",
            description="A 2D vector (x, y).",
            x=0.0,
            y=0.0,
        ),

        # -----------------------------------------------------------------------
        # Shape Parameters (UI overlays, support keyable per-view values)
        # -----------------------------------------------------------------------
        desc.Point2d(
            name="point2d",
            label="Point 2D",
            description="A single 2D point overlay.",
        ),
        desc.Line2d(
            name="line2d",
            label="Line 2D",
            description="A 2D line defined by two points.",
        ),
        desc.Rectangle(
            name="rectangle",
            label="Rectangle",
            description="An axis-aligned 2D rectangle.",
        ),
        desc.Circle(
            name="circle",
            label="Circle",
            description="A circle defined by center and radius.",
        ),
        desc.ShapeList(
            name="pointList",
            label="Point List",
            description="A list of 2D points.",
            shape=desc.Point2d(name="pt", label="Point", description=""),
        ),

        # -----------------------------------------------------------------------
        # Keyable Attribute (per-view value)
        # -----------------------------------------------------------------------
        desc.FloatParam(
            name="keyableFloat",
            label="Keyable Float",
            description="A float that supports per-key (per-view) values.",
            value=1.0,
            range=(0.0, 2.0, 0.01),
            keyable=True,
        ),
    ]

    outputs = [

        # -----------------------------------------------------------------------
        # Static File Output (path expression)
        # -----------------------------------------------------------------------
        desc.File(
            name="outputFile",
            label="Output File",
            description="A statically defined output file path (expression-based).",
            value="{nodeCacheFolder}/output.txt",
        ),
        desc.File(
            name="outputDir",
            label="Output Directory",
            description="A statically defined output directory.",
            value="{nodeCacheFolder}/",
        ),

        # -----------------------------------------------------------------------
        # Dynamic Outputs (value computed at runtime)
        # -----------------------------------------------------------------------
        desc.IntParam(
            name="outputInt",
            label="Output Integer",
            description="Dynamically computed integer output.",
            value=None,
        ),
        desc.FloatParam(
            name="outputFloat",
            label="Output Float",
            description="Dynamically computed float output.",
            value=None,
        ),
        desc.BoolParam(
            name="outputBool",
            label="Output Bool",
            description="Dynamically computed boolean output.",
            value=None,
        ),
        desc.StringParam(
            name="outputString",
            label="Output String",
            description="Dynamically computed string output.",
            value=None,
        ),
        desc.ColorParam(
            name="outputColor",
            label="Output Color",
            description="Dynamically computed color output.",
            value=None,
        ),
    ]

    def process(self, node):
        pass
