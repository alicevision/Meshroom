from meshroom.core.desc import GroupAttribute, ValueTypeErrors
from meshroom.common import Property, Variant


class AnySet(GroupAttribute):

    def __init__(self,
                 name="Custom Attributes",
                 label=None,
                 description=None,
                 commandLineGroup="allParams",
                 advanced=False, semantic="",
                 enabled=True,
                 visible=True,
                 exposed=False):

        super().__init__(items = [],
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

    isCustomAttribute = Property(bool, lambda _: True, constant=True)
