from meshroom.core.desc.attribute import Attribute, ValueTypeErrors


class DotAttribute(Attribute):
    """
    Type-agnostic attribute used by Dot nodes.

    A Dot node declares one input and one output of this type. The attribute accepts
    connections of any type and holds no value of its own: the value of the Dot output
    is the value of the Dot input, and the type reported by the Dot output follows the
    type of the attribute connected to the Dot input (so that connecting through a Dot
    behaves exactly like a direct connection).
    """

    def __init__(self, name, label=None, description=None, value="", advanced=False, semantic="",
                 enabled=True, invalidate=True, visible=True, exposed=False, validators=None):
        super(DotAttribute, self).__init__(name=name, label=label, description=description, value=value,
                                           commandLineGroup="", advanced=advanced, enabled=enabled,
                                           invalidate=invalidate, semantic=semantic, visible=visible,
                                           exposed=exposed, validators=validators)

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import DotAttribute
        return DotAttribute

    def validateValue(self, value):
        """ Accept any value: the type of a Dot attribute follows its connections. """
        return value

    def checkValueTypes(self):
        return "", ValueTypeErrors.NONE
