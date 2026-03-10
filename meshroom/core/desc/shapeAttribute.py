from meshroom.core.desc import ListAttribute, GroupAttribute, StringParam, FloatParam, Geometry, Size2d, Vec2d

class Shape(GroupAttribute):
    """
    Base attribute for all Shape attribute.
    Countains several attributes (inherit from GroupAttribute).
    """
    def __init__(self, geometryItems, name, label, description, commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        items = [
            StringParam(name="userName", label="User Name", description="User shape name.", value="",
                        commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            StringParam(name="userColor", label="User Color", description="User shape color.", value="#2a82da",
                        commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            Geometry(geometryItems, name="geometry", label="Geometry", description="Shape geometry.",
                     commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # GroupAttribute constructor
        super(Shape, self).__init__(items=items, name=name, label=label, description=description,
                                    commandLineGroup=commandLineGroup, advanced=advanced, semantic=semantic,
                                    enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        """
        Return the correct Attribute instance corresponding to the description.
        """
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import ShapeAttribute
        return ShapeAttribute

class ShapeList(ListAttribute):
    """
    List attribute of Shape attribute.
    Countains several attributes (inherit from ListAttribute).
    """
    def __init__(self, shape: Shape, name, label, description, commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # ListAttribute constructor
        super(ShapeList, self).__init__(elementDesc=shape, name=name, label=label, description=description,
                                        commandLineGroup=commandLineGroup, advanced=advanced, semantic=semantic,
                                        enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        """
        Return the correct Attribute instance corresponding to the description.
        """
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import ShapeListAttribute
        return ShapeListAttribute

class Point2d(Shape):
    """
    Point2d is a Shape attribute that allows to display and modify a 2d point.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None,
                 commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        geometryItems = [
            FloatParam(name="x", label="X", description="X coordinate.", value=-1.0, keyable=keyable, keyType=keyType,
                       commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="y", label="Y", description="Y coordinate.", value=-1.0, keyable=keyable, keyType=keyType,
                       commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Point2d, self).__init__(geometryItems, name, label, description, commandLineGroup=None, advanced=advanced,
                                      semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)

class Line2d(Shape):
    """
    Line2d is a Shape attribute that allows to display and modify a 2d line.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None,
                 commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        geometryItems = [
            Vec2d(name="a", label="A", description="Line A point.", x=-1.0, y=-1.0, keyable=keyable, keyType=keyType,
                  commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            Vec2d(name="b", label="B", description="Line B point.", x=-1.0, y=-1.0, keyable=keyable, keyType=keyType,
                  commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Line2d, self).__init__(geometryItems, name, label, description, commandLineGroup=None, advanced=advanced,
                                     semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)

class Rectangle(Shape):
    """
    Rectangle is a Shape attribute that allows to display and modify a rectangle.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None,
                 commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        geometryItems = [
            Vec2d(name="center", label="Center", description="Rectangle center.", x=-1.0, y=-1.0,
                  keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                  enabled=enabled, visible=visible, exposed=exposed),
            Size2d(name="size", label="Size", description="Rectangle size.", width=-1.0, height=-1.0,
                   keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                   enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Rectangle, self).__init__(geometryItems, name, label, description, commandLineGroup=None, advanced=advanced,
                                        semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)

class Circle(Shape):
    """
    Circle is a Shape attribute that allows to display and modify a circle.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None,
                 commandLineGroup="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Geometry group desciption
        geometryItems = [
            Vec2d(name="center", label="Center", description="Circle center.", x=-1.0, y=-1.0,
                  keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                  enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="radius", label="Radius", description="Circle radius.", value=-1.0,
                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                       enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Circle, self).__init__(geometryItems, name, label, description, commandLineGroup=None, advanced=advanced,
                                     semantic=semantic, enabled=enabled, visible=visible, exposed=exposed)