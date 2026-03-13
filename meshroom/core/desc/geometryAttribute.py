from meshroom.core.desc import GroupAttribute, FloatParam


class Geometry(GroupAttribute):
    """
    Base attribute for all Geometry attribute.
    Countains several attributes (inherit from GroupAttribute).
    """
    def __init__(self, items, name, label=None, description=None, commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # GroupAttribute constructor
        super(Geometry, self).__init__(items=items, name=name, label=label, description=description,
                                       commandLineGroup=commandLineGroup, advanced=advanced, semantic=semantic,
                                       enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        """
        Return the correct Attribute instance corresponding to the description.
        """
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import GeometryAttribute
        return GeometryAttribute


class Size2d(Geometry):
    """
    Size2d is a Geometry attribute that allows to specify a 2d size.
    """
    def __init__(self, name, label=None, description=None, width=None, height=None, widthRange=None, heightRange=None,
                 keyable=False, keyType=None, commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        items = [
            FloatParam(name="width", label="Width", description="Width size.", value=width, range=widthRange,
                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                       enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="height", label="Height", description="Height size.", value=height, range=heightRange,
                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                       enabled=enabled, visible=visible, exposed=exposed)
        ]
        # GeometryAttribute constructor
        super(Size2d, self).__init__(items, name, label, description, commandLineGroup=None, advanced=advanced,
                                     semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)

class Vec2d(Geometry):
    """
    Vec2d is a Geometry attribute that allows to specify a 2d vector.
    """
    def __init__(self, name, label=None, description=None, x=None, y=None, xRange=None, yRange=None,
                 keyable=False, keyType=None, commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        items = [
            FloatParam(name="x", label="X", description="X coordinate.", value=x, range=xRange,
                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                       enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="y", label="Y", description="Y coordinate.", value=y, range=yRange,
                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                       enabled=enabled, visible=visible, exposed=exposed)
        ]
        # GeometryAttribute constructor
        super(Vec2d, self).__init__(items, name, label, description, commandLineGroup=None, advanced=advanced,
                                     semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)
