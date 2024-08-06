from meshroom.common import BaseObject, Property, Variant, VariantList, JSValue
from meshroom.core import attribute, desc


class JobAttribute(attribute.ChoiceParam):
    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        super(JobAttribute, self).__init__(node, attributeDesc, isOutput, root, parent)
        print("Constructor for JobParam")

    def update(self):
        print("Updating in JobParam, about to replace list of available params")
        newValues = ["c", "d", "e", "f"]
        self.setValues(newValues)


class JobParam(desc.ChoiceParam):
    def __init__(self, name, label, description, value, values, exclusive, uid, group='allParams', joinChar=' ', advanced=False, semantic='',
                 enabled=True, validValue=True, errorMessage="", visible=True):
        assert values
        super(JobParam, self).__init__(name=name, label=label, description=description, value=value, values=values, exclusive=exclusive, uid=uid, group=group, joinChar=joinChar, advanced=advanced, semantic=semantic, enabled=enabled, validValue=validValue, errorMessage=errorMessage, visible=visible)

        self._attrType = JobAttribute

    type = Property(str, lambda self: self.__class__.__base__.__name__, constant=True)
