from meshroom.core.desc import GroupAttribute, ValueTypeErrors
from meshroom.common import Property, Variant


class AnySet(GroupAttribute):

    def __init__(self,
                 name="Custom Attributes",
                 items=None,
                 label=None,
                 description=None,
                 commandLineGroup="allParams",
                 advanced=False,
                 semantic="",
                 enabled=True,
                 visible=True,
                 exposed=False):

        super().__init__(items = items if items is not None else [],
                         name=name,
                         label=label,
                         description=description,
                         commandLineGroup=commandLineGroup,
                         advanced=advanced,
                         semantic=semantic,
                         enabled=enabled,
                         visible=visible,
                         exposed=exposed)

    def checkValueTypes(self):
        return "", ValueTypeErrors.NONE

    def getInstanceType(self):
        from meshroom.core.attribute import AnySet
        return AnySet

    def validateValue(self, value):
        return value

    # Override
    def clone(self):
        return self.__class__(items=[item.clone() for item in self._items],
                              name=self.name,
                              label=self.label,
                              description=self.description,
                              commandLineGroup=self.commandLineGroup,
                              advanced=self.advanced,
                              semantic=self.semantic,
                              enabled=self.enabled,
                              visible=self.visible,
                              exposed=self.exposed)

    # Override
    def shortDesc(self) -> dict:
        serializedData = {
            "type": self.__class__.__name__,
            "name": self.name,
            "items": {}
        }
        return serializedData

    isCustomAttribute = Property(bool, lambda _: True, constant=True)
    # Override
    # A GroupAttribute is invalidating if any of its items is, but an AnySet has no predefined items:
    # its children are user-defined, so it must always be taken into account in the node UID.
    invalidate = Property(bool, lambda _: True, constant=True)
