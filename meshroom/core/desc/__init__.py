from .attribute import (
    Attribute,
    BoolParam,
    ChoiceParam,
    ColorParam,
    File,
    FloatParam,
    GroupAttribute,
    IntParam,
    ListAttribute,
    PushButtonParam,
    StringParam,
    ValueTypeErrors,
)
from .geometryAttribute import (
    Geometry,
    Size2d,
    Vec2d,
)
from .shapeAttribute import (
    Shape,
    ShapeList,
    Point2d,
    Line2d,
    Rectangle,
    Circle
)
from .dynamicAttribute import (
    DynamicAttribute,
    CustomAttributes
)
from .computation import (
    DynamicNodeSize,
    Level,
    MultiDynamicNodeSize,
    Parallelization,
    Range,
    StaticNodeSize,
)
from .node import (
    AVCommandLineNode,
    BaseNode,
    BackdropNode,
    CommandLineNode,
    InitNode,
    InputNode,
    InternalAttributesFactory,
    MrNodeType,
    Node,
)

STR_TO_ATTRIBUTE_DESCRIPTION = {
    'Attribute': Attribute,
    'BoolParam': BoolParam,
    'ChoiceParam': ChoiceParam,
    'ColorParam': ColorParam,
    'File': File,
    'FloatParam': FloatParam,
    'GroupAttribute': GroupAttribute,
    'IntParam': IntParam,
    'ListAttribute': ListAttribute,
    'PushButtonParam': PushButtonParam,
    'StringParam': StringParam
}