from meshroom.core.desc import ListAttribute, GroupAttribute, FloatParam

class Shape(GroupAttribute):
    """ 
    Base attribute for all Shape attribute.
    Countains several attributes (inherit from GroupAttribute).
    """
    def __init__(self, groupDesc, name, label, description, group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # GroupAttribute constructor
        super(Shape, self).__init__(groupDesc=groupDesc, name=name, label=label, description=description,
                                    group=group, advanced=advanced, semantic=semantic,
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
    def __init__(self, shape: Shape, name, label, description, group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # ListAttribute constructor
        super(ShapeList, self).__init__(elementDesc=shape, name=name, label=label, description=description, 
                                        group=group, advanced=advanced, semantic=semantic, 
                                        enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        """ 
        Return the correct Attribute instance corresponding to the description. 
        """
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import ShapeListAttribute
        return ShapeListAttribute

class Size2d(Shape):
    """
    Size2d is a Shape attribute that allows to specify a 2d size.
    Note: This attribute is not displayable.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None, 
                 group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        groupDesc = [
            FloatParam(name="width", label="Width", description="Width size.", value=-1.0, keyable=keyable, keyType=keyType, 
                       group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="height", label="Height", description="Height size.", value=-1.0, keyable=keyable, keyType=keyType, 
                       group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Size2d, self).__init__(groupDesc, name, label, description, group=None, advanced=advanced, semantic=semantic,
                                      enabled=enabled, visible=visible, exposed=exposed)

class Point2d(Shape):
    """
    Point2d is a Shape attribute that allows to display and modify a 2d point.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None, 
                 group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        groupDesc = [
            FloatParam(name="x", label="X", description="X coordinate.", value=-1.0, keyable=keyable, keyType=keyType, 
                       group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="y", label="Y", description="Y coordinate.", value=-1.0, keyable=keyable, keyType=keyType, 
                       group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Point2d, self).__init__(groupDesc, name, label, description, group=None, advanced=advanced, semantic=semantic,
                                      enabled=enabled, visible=visible, exposed=exposed)

class Line2d(Shape):
    """
    Line2d is a Shape attribute that allows to display and modify a 2d line.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None, 
                 group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        groupDesc = [
            Point2d(name="a", label="A", description="Line A point.", keyable=keyable, keyType=keyType, 
                    group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            Point2d(name="b", label="B", description="Line B point.", keyable=keyable, keyType=keyType, 
                    group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Line2d, self).__init__(groupDesc, name, label, description, group=None, advanced=advanced, semantic=semantic,
                                      enabled=enabled, visible=visible, exposed=exposed)

class Rectangle(Shape):
    """
    Rectangle is a Shape attribute that allows to display and modify a rectangle.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None, 
                 group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        groupDesc = [
            Point2d(name="center", label="Center", description="Rectangle center.", keyable=keyable, keyType=keyType, 
                    group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            Size2d(name="size", label="Size", description="Rectangle size.", keyable=keyable, keyType=keyType, 
                    group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Rectangle, self).__init__(groupDesc, name, label, description, group=None, advanced=advanced, semantic=semantic,
                                      enabled=enabled, visible=visible, exposed=exposed)

class Circle(Shape):
    """
    Circle is a Shape attribute that allows to display and modify a circle.
    """
    def __init__(self, name, label, description, keyable=False, keyType=None, 
                 group="allParams", advanced=False, semantic="",
                 enabled=True, visible=True, exposed=False):
        # Shape group desciption
        groupDesc = [
            Point2d(name="center", label="Center", description="Circle center.", keyable=keyable, keyType=keyType, 
                    group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed),
            FloatParam(name="radius", label="Radius", description="Circle radius.", value=-1.0, keyable=keyable, keyType=keyType, 
                       group=group, advanced=advanced, enabled=enabled, visible=visible, exposed=exposed)
        ]
        # ShapeAttribute constructor
        super(Circle, self).__init__(groupDesc, name, label, description, group=None, advanced=advanced, semantic=semantic,
                                      enabled=enabled, visible=visible, exposed=exposed)