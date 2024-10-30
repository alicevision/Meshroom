import ast
import distutils.util
import os
import types
from collections.abc import Iterable

from meshroom.common import BaseObject, JSValue, Property, Variant, VariantList


class Attribute(BaseObject):
    """
    """

    def __init__(self, name, label, description, value, advanced, semantic, group, enabled, invalidate=True,
                 uidIgnoreValue=None, validValue=True, errorMessage="", visible=True, exposed=False):
        super(Attribute, self).__init__()
        self._name = name
        self._label = label
        self._description = description
        self._value = value
        self._group = group
        self._advanced = advanced
        self._enabled = enabled
        self._invalidate = invalidate
        self._semantic = semantic
        self._uidIgnoreValue = uidIgnoreValue
        self._validValue = validValue
        self._errorMessage = errorMessage
        self._visible = visible
        self._exposed = exposed
        self._isExpression = (isinstance(self._value, str) and "{" in self._value) \
            or isinstance(self._value, types.FunctionType)
        self._isDynamicValue = (self._value is None)
        self._valueType = None

    def getInstanceType(self):
        """ Return the correct Attribute instance corresponding to the description. """
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import Attribute
        return Attribute

    def validateValue(self, value):
        """ Return validated/conformed 'value'. Need to be implemented in derived classes.

        Raises:
            ValueError: if value does not have the proper type
        """
        raise NotImplementedError("Attribute.validateValue is an abstract function that should be "
                                  "implemented in the derived class.")

    def checkValueTypes(self):
        """ Returns the attribute's name if the default value's type is invalid or if the range's type (when available)
        is invalid, empty string otherwise.

        Returns:
            string: the attribute's name if the default value's or range's type is invalid, empty string otherwise
        """
        raise NotImplementedError("Attribute.checkValueTypes is an abstract function that should be implemented in the "
                                  "derived class.")

    def matchDescription(self, value, strict=True):
        """ Returns whether the value perfectly match attribute's description.

        Args:
            value: the value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)
        """
        try:
            self.validateValue(value)
        except ValueError:
            return False
        return True

    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    # isExpression:
    #   The default value of the attribute's descriptor is a static string expression that should be evaluated at runtime.
    #   This property only makes sense for output attributes.
    isExpression = Property(bool, lambda self: self._isExpression, constant=True)
    # isDynamicValue
    #   The default value of the attribute's descriptor is None, so it's not an input value,
    #   but an output value that is computed during the Node's process execution.
    isDynamicValue = Property(bool, lambda self: self._isDynamicValue, constant=True)
    group = Property(str, lambda self: self._group, constant=True)
    advanced = Property(bool, lambda self: self._advanced, constant=True)
    enabled = Property(Variant, lambda self: self._enabled, constant=True)
    invalidate = Property(Variant, lambda self: self._invalidate, constant=True)
    semantic = Property(str, lambda self: self._semantic, constant=True)
    uidIgnoreValue = Property(Variant, lambda self: self._uidIgnoreValue, constant=True)
    validValue = Property(Variant, lambda self: self._validValue, constant=True)
    errorMessage = Property(str, lambda self: self._errorMessage, constant=True)
    # visible:
    #   The attribute is not displayed in the Graph Editor if False but still visible in the Node Editor.
    #   This property is useful to hide some attributes that are not relevant for the user.
    visible = Property(bool, lambda self: self._visible, constant=True)
    # exposed:
    #   The attribute is exposed in the upper part of the node in the Graph Editor.
    #   By default, all file attributes are exposed.
    exposed = Property(bool, lambda self: self._exposed, constant=True)
    type = Property(str, lambda self: self.__class__.__name__, constant=True)
    # instanceType
    #   Attribute instance corresponding to the description
    instanceType = Property(Variant, lambda self: self.getInstanceType(), constant=True)


class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, name, label, description, group="allParams", advanced=False, semantic="",
                 enabled=True, joinChar=" ", visible=True, exposed=False):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self._elementDesc = elementDesc
        self._joinChar = joinChar
        super(ListAttribute, self).__init__(name=name, label=label, description=description, value=[],
                                            invalidate=False, group=group, advanced=advanced, semantic=semantic,
                                            enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import ListAttribute
        return ListAttribute

    def validateValue(self, value):
        if value is None:
            return value
        if JSValue is not None and isinstance(value, JSValue):
            # Note: we could use isArray(), property("length").toInt() to retrieve all values
            raise ValueError("ListAttribute.validateValue: cannot recognize QJSValue. "
                             "Please, use JSON.stringify(value) in QML.")
        if isinstance(value, str):
            # Alternative solution to set values from QML is to convert values to JSON string
            # In this case, it works with all data types
            value = ast.literal_eval(value)

        if not isinstance(value, (list, tuple)):
            raise ValueError("ListAttribute only supports list/tuple input values "
                             "(param:{}, value:{}, type:{})".format(self.name, value, type(value)))
        return value

    def checkValueTypes(self):
        return self.elementDesc.checkValueTypes()

    def matchDescription(self, value, strict=True):
        """ Check that 'value' content matches ListAttribute's element description. """
        if not super(ListAttribute, self).matchDescription(value, strict):
            return False
        # list must be homogeneous: only test first element
        if value:
            return self._elementDesc.matchDescription(value[0], strict)
        return True

    elementDesc = Property(Attribute, lambda self: self._elementDesc, constant=True)
    invalidate = Property(Variant, lambda self: self.elementDesc.invalidate, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, name, label, description, group="allParams", advanced=False, semantic="",
                 enabled=True, joinChar=" ", brackets=None, visible=True, exposed=False):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self._groupDesc = groupDesc
        self._joinChar = joinChar
        self._brackets = brackets
        super(GroupAttribute, self).__init__(name=name, label=label, description=description, value={},
                                             group=group, advanced=advanced, invalidate=False, semantic=semantic,
                                             enabled=enabled, visible=visible, exposed=exposed)

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import GroupAttribute
        return GroupAttribute

    def validateValue(self, value):
        """ Ensure value is compatible with the group description and convert value if needed. """
        if value is None:
            return value
        if JSValue is not None and isinstance(value, JSValue):
            # Note: we could use isArray(), property("length").toInt() to retrieve all values
            raise ValueError("GroupAttribute.validateValue: cannot recognize QJSValue. "
                             "Please, use JSON.stringify(value) in QML.")
        if isinstance(value, str):
            # Alternative solution to set values from QML is to convert values to JSON string
            # In this case, it works with all data types
            value = ast.literal_eval(value)

        if isinstance(value, dict):
            # invalidKeys = set(value.keys()).difference([attr.name for attr in self._groupDesc])
            # if invalidKeys:
            #     raise ValueError('Value contains key that does not match group description : {}'.format(invalidKeys))
            if self._groupDesc and value.keys():
                commonKeys = set(value.keys()).intersection([attr.name for attr in self._groupDesc])
                if not commonKeys:
                    raise ValueError(f"Value contains no key that matches with the group description "
                                     f"(name={self.name}, values={value.keys()}, "
                                     f"desc={[attr.name for attr in self._groupDesc]})")
        elif isinstance(value, (list, tuple, set)):
            if len(value) != len(self._groupDesc):
                raise ValueError("Value contains incoherent number of values: desc size: {}, value size: {}".
                                 format(len(self._groupDesc), len(value)))
        else:
            raise ValueError("GroupAttribute only supports dict/list/tuple input values (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))

        return value

    def checkValueTypes(self):
        """ Check the default value's and range's (if available) type of every attribute contained in the group
        (including nested attributes).

        Returns an empty string if all the attributes' types are valid, or concatenates the names of the attributes in
        the group with invalid types.
        """
        invalidParams = []
        for attr in self.groupDesc:
            name = attr.checkValueTypes()
            if name:
                invalidParams.append(name)
        if invalidParams:
            # In group "group", if parameters "x" and "y" (with "y" in nested group "subgroup") are invalid, the
            # returned string will be: "group:x, group:subgroup:y"
            return self.name + ":" + str(", " + self.name + ":").join(invalidParams)
        return ""

    def matchDescription(self, value, strict=True):
        """
        Check that 'value' contains the exact same set of keys as GroupAttribute's group description
        and that every child value match corresponding child attribute description.

        Args:
            value: the value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)
        """
        if not super(GroupAttribute, self).matchDescription(value):
            return False
        attrMap = {attr.name: attr for attr in self._groupDesc}

        matchCount = 0
        for k, v in value.items():
            # each child value must match corresponding child attribute description
            if k in attrMap and attrMap[k].matchDescription(v, strict):
                matchCount += 1

        if strict:
            return matchCount == len(value.items()) == len(self._groupDesc)

        return matchCount > 0

    def retrieveChildrenInvalidations(self):
        allInvalidations = []
        for desc in self._groupDesc:
            allInvalidations.append(desc.invalidate)
        return allInvalidations

    groupDesc = Property(Variant, lambda self: self._groupDesc, constant=True)
    invalidate = Property(Variant, retrieveChildrenInvalidations, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)
    brackets = Property(str, lambda self: self._brackets, constant=True)


class Param(Attribute):
    """
    """
    def __init__(self, name, label, description, value, group, advanced, semantic, enabled, invalidate=True,
                 uidIgnoreValue=None, validValue=True, errorMessage="", visible=True, exposed=False):
        super(Param, self).__init__(name=name, label=label, description=description, value=value,
                                    group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                    semantic=semantic, uidIgnoreValue=uidIgnoreValue, validValue=validValue,
                                    errorMessage=errorMessage, visible=visible, exposed=exposed)


class File(Attribute):
    """
    """
    def __init__(self, name, label, description, value, group="allParams", advanced=False, invalidate=True,
                 semantic="", enabled=True, visible=True, exposed=True):
        super(File, self).__init__(name=name, label=label, description=description, value=value, group=group,
                                   advanced=advanced, enabled=enabled, invalidate=invalidate, semantic=semantic,
                                   visible=visible, exposed=exposed)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError("File only supports string input  (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))
        return os.path.normpath(value).replace("\\", "/") if value else ""

    def checkValueTypes(self):
        # Some File values are functions generating a string: check whether the value is a string or if it
        # is a function (but there is no way to check that the function's output is indeed a string)
        if not isinstance(self.value, str) and not callable(self.value):
            return self.name
        return ""


class BoolParam(Param):
    """
    """
    def __init__(self, name, label, description, value, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False):
        super(BoolParam, self).__init__(name=name, label=label, description=description, value=value,
                                        group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                        semantic=semantic, visible=visible, exposed=exposed)
        self._valueType = bool

    def validateValue(self, value):
        if value is None:
            return value
        try:
            if isinstance(value, str):
                # use distutils.util.strtobool to handle (1/0, true/false, on/off, y/n)
                return bool(distutils.util.strtobool(value))
            return bool(value)
        except Exception:
            raise ValueError("BoolParam only supports bool value (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))

    def checkValueTypes(self):
        if not isinstance(self.value, bool):
            return self.name
        return ""


class IntParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range=None, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", validValue=True, errorMessage="", visible=True, exposed=False):
        self._range = range
        super(IntParam, self).__init__(name=name, label=label, description=description, value=value,
                                       group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                       semantic=semantic, validValue=validValue, errorMessage=errorMessage,
                                       visible=visible, exposed=exposed)
        self._valueType = int

    def validateValue(self, value):
        if value is None:
            return value
        # Handle unsigned int values that are translated to int by shiboken and may overflow
        try:
            return int(value)
        except Exception:
            raise ValueError("IntParam only supports int value (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))

    def checkValueTypes(self):
        if not isinstance(self.value, int) or (self.range and not all([isinstance(r, int) for r in self.range])):
            return self.name
        return ""

    range = Property(VariantList, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range=None, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", validValue=True, errorMessage="", visible=True, exposed=False):
        self._range = range
        super(FloatParam, self).__init__(name=name, label=label, description=description, value=value,
                                         group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                         semantic=semantic, validValue=validValue, errorMessage=errorMessage,
                                         visible=visible, exposed=exposed)
        self._valueType = float

    def validateValue(self, value):
        if value is None:
            return value
        try:
            return float(value)
        except Exception:
            raise ValueError("FloatParam only supports float value (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))

    def checkValueTypes(self):
        if not isinstance(self.value, float) or (self.range and not all([isinstance(r, float) for r in self.range])):
            return self.name
        return ""

    range = Property(VariantList, lambda self: self._range, constant=True)


class PushButtonParam(Param):
    """
    """
    def __init__(self, name, label, description, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False):
        super(PushButtonParam, self).__init__(name=name, label=label, description=description, value=None,
                                              group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                              semantic=semantic, visible=visible, exposed=exposed)
        self._valueType = None

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import PushButtonParam
        return PushButtonParam

    def validateValue(self, value):
        return value

    def checkValueTypes(self):
        pass


class ChoiceParam(Param):
    """
    """
    def __init__(self, name, label, description, value, values, exclusive=True, group="allParams", joinChar=" ",
                 advanced=False, enabled=True, invalidate=True, semantic="", validValue=True, errorMessage="",
                 visible=True, exposed=False):
        assert values
        super(ChoiceParam, self).__init__(name=name, label=label, description=description, value=value,
                                          group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                          semantic=semantic, validValue=validValue, errorMessage=errorMessage,
                                          visible=visible, exposed=exposed)
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        if self._values:
            # Look at the type of the first element of the possible values
            self._valueType = type(self._values[0])
        elif not exclusive:
            # Possible values may be defined later, so use the value to define the type.
            # if non exclusive, it is a list
            self._valueType = type(self._value[0])
        else:
            self._valueType = type(self._value)

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import ChoiceParam
        return ChoiceParam

    def conformValue(self, value):
        """ Conform 'value' to the correct type and check for its validity """
        # We do not check that the value is in the list of values.
        # This allows to have a value that is not in the list of possible values.
        return self._valueType(value)

    def validateValue(self, value):
        if value is None:
            return value
        if self.exclusive:
            return self.conformValue(value)

        if isinstance(value, str):
            value = value.split(',')

        if not isinstance(value, Iterable):
            raise ValueError("Non-exclusive ChoiceParam value should be iterable (param: {}, value: {}, type: {}).".
                             format(self.name, value, type(value)))

        return [self.conformValue(v) for v in value]

    def checkValueTypes(self):
        # Check that the values have been provided as a list
        if not isinstance(self._values, list):
            return self.name

        # If the choices are not exclusive, check that 'value' is a list, and check that it does not contain values that
        # are not available
        elif not self.exclusive and (not isinstance(self._value, list) or
                                     not all(val in self._values for val in self._value)):
            return self.name

        # If the choices are exclusive, the value should NOT be a list but it can contain any value that is not in the
        # list of possible ones
        elif self.exclusive and isinstance(self._value, list):
            return self.name

        return ""

    values = Property(VariantList, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    def __init__(self, name, label, description, value, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", uidIgnoreValue=None, validValue=True, errorMessage="", visible=True,
                 exposed=False):
        super(StringParam, self).__init__(name=name, label=label, description=description, value=value,
                                          group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                          semantic=semantic, uidIgnoreValue=uidIgnoreValue, validValue=validValue,
                                          errorMessage=errorMessage, visible=visible, exposed=exposed)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError("StringParam value should be a string (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))
        return value

    def checkValueTypes(self):
        if not isinstance(self.value, str):
            return self.name
        return ""


class ColorParam(Param):
    """
    """
    def __init__(self, name, label, description, value, group="allParams", advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False):
        super(ColorParam, self).__init__(name=name, label=label, description=description, value=value,
                                         group=group, advanced=advanced, enabled=enabled, invalidate=invalidate,
                                         semantic=semantic, visible=visible, exposed=exposed)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str) or len(value.split(" ")) > 1:
            raise ValueError('ColorParam value should be a string containing either an SVG name or an hexadecimal '
                             'color code (param: {}, value: {}, type: {})'.format(self.name, value, type(value)))
        return value

