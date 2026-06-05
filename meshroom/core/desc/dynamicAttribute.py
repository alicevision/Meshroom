from meshroom.core.desc import GroupAttribute, Attribute, ValueTypeErrors

from typing import Optional
from meshroom.common import Property, Variant


class DynamicAttribute(Attribute):
    """
    A DynamicAttribute is a special input attribute with no fixed type.
    It appears as an empty connection pin in the graph editor (no label).
    When an attribute is connected to it, a new attribute of the same type as the
    connected attribute is automatically created on the node and the link is established.
    The DynamicAttribute itself remains empty and available for further connections.
    """
    def __init__(self, 
                 name="Customs", 
                 label=None, 
                 description=None,
                 commandLineGroup=None, 
                 advanced=False, 
                 enabled=True,
                 visible=True, 
                 exposed=False):
        super().__init__(
            name=name, label=label, description=description or "", value=None,
            commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
            invalidate=False, semantic="", visible=visible, exposed=exposed,
        )

        self._attribute: Optional[Attribute] = None

    def getAttribute(self) -> Attribute:
        return self._attribute

    def getInstanceType(self):
        from meshroom.core.attribute import DynamicAttribute
        return DynamicAttribute

    def validateValue(self, value):
        return value

    def checkValueTypes(self): 
        return "", ValueTypeErrors.NONE


class CustomAttributes(GroupAttribute):

    def __init__(self, 
                 name="Custom Attributes", 
                 label=None, 
                 description=None, 
                 commandLineGroup="allParams", 
                 advanced=False, semantic="",  
                 enabled=True,
                 visible=True,
                 exposed=False):

        super().__init__(items = [DynamicAttribute(name="hello", label="(+)", description="")],
                         name=name, 
                         label=label, 
                         description=description, 
                         commandLineGroup=commandLineGroup, 
                         advanced=advanced, 
                         semantic=semantic, 
                         enabled=enabled, 
                         visible=visible, 
                         exposed=exposed)
    
    def addDynamicInput(self, attrName, srcDesc, dynAttr):
        """
        Create and register a dynamic input attribute based on *srcDesc* and
        insert it before *dynAttr* in the node's attribute list.

        Args:
            attrName: Unique name for the new attribute.
            srcDesc: Attribute descriptor to clone (the type of the created attr).
            dynAttr: The DynamicAttribute before which to insert the new attr.

        Returns:
            The newly created Attribute instance.
        """
        import copy as _copy
        from meshroom.core.node import attributeFactory

        descCopy = _copy.deepcopy(srcDesc)
        descCopy._name = attrName

        newAttr = attributeFactory(descCopy, None, isOutput=False, node=self)
        newAttr._isDynamic = True

        dynIdx = next(
            (i for i, a in enumerate(self._attributes) if a is dynAttr),
            len(list(self._attributes)),
        )
        self._attributes.insert(dynIdx, newAttr)

        if newAttr.invalidate:
            self.invalidatingAttributes.add(newAttr)

        return newAttr

    def checkValueTypes(self):
        return "", ValueTypeErrors.NONE

    def getInstanceType(self):
        from meshroom.core.attribute import CustomAttributes
        return CustomAttributes

    def validateValue(self, value):
        return value
