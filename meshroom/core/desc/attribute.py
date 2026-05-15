import ast
import os
import re
from collections.abc import Iterable
from enum import auto, Enum
from typing import Sequence

from meshroom.common import BaseObject, JSValue, Property, Variant, VariantList, strtobool, deprecated
from meshroom.core.desc.validators import AttributeValidator

# Pre-compile regexes for better performance on repeated calls
_ACRONYM_RE = re.compile(r'([A-Z]+)([A-Z][a-z])')
_CAMEL_CASE_RE = re.compile(r'([a-z\d])([A-Z])')
_SPLIT_RE = re.compile(r'[_\s]+')

def convertToLabel(name: str) -> str:
    """Convert a camelCase or snake_case attribute name into a human-readable label.
    
    Examples:
        >>> convertToLabel('camelCase')
        'Camel Case'
        >>> convertToLabel('snake_case')
        'Snake Case'
        >>> convertToLabel('myURLParser')
        'My URL Parser'
        >>> convertToLabel('mixed_caseExample')
        'Mixed Case Example'
        >>> convertToLabel('')
        ''
    """
    if not name:
        return ''
    
    # Handle consecutive uppercase letters (e.g. 'URL', 'HTTP')
    name = _ACRONYM_RE.sub(r'\1 \2', name)
    # Insert space between camelCase boundaries
    name = _CAMEL_CASE_RE.sub(r'\1 \2', name)
    # Split on underscores or spaces
    words = _SPLIT_RE.split(name)
    
    # Preserve uppercase acronyms, capitalize others
    return ' '.join(
        word if word.isupper() else word.capitalize()
        for word in words
        if word
    )

class ValueTypeErrors(Enum):
    NONE = auto()  # No error
    TYPE = auto()  # Invalid type
    RANGE = auto()  # Invalid range
    DYNAMIC_OUTPUT = auto()  # Dynamic output not supported

"""
This object is used in group/commandLineGroup to check if
the parameter has been set by the user (None is a valid parameter passed value)
"""
_setParamSentinel = object()

class Attribute(BaseObject):
    """
    """

    def __init__(self, name, label, description, value, advanced, semantic, commandLineGroup, enabled,
                 keyable=False, keyType=None, invalidate=True, uidIgnoreValue=None, visible=True, exposed=False, validators: Sequence[AttributeValidator]=None):
        super(Attribute, self).__init__()
        self._name = name
        self._label = convertToLabel(name) if label is None else label
        self._description = "" if description is None else description
        self._value = value
        self._keyable = keyable
        self._keyType = keyType
        self._commandLineGroup = commandLineGroup
        self._advanced = advanced
        self._enabled = enabled
        self._invalidate = invalidate
        self._semantic = semantic
        self._uidIgnoreValue = uidIgnoreValue
        self._visible = visible
        self._exposed = exposed
        self._isExpression = (isinstance(self._value, str) and "{" in self._value) \
            or callable(self._value)
        self._isDynamicValue = (self._value is None)
        self._valueType = None

        if validators is None:
            self._validators = []
        elif isinstance(validators, Sequence) and all(isinstance(x, AttributeValidator) for x in validators):
            self._validators = validators
        else:
            raise RuntimeError(f"Validators should be of type 'Sequence[AttributeValidator]', the type '{type(validators)}' is not supported.")
        
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

    def validateKeyValues(self, keyValues):
        """ Return validated/conformed 'keyValues'.

        Raises:
            ValueError: if a value does not have the proper type
        """
        return isinstance(keyValues, dict) and \
               all(isinstance(k, str) and self.validateValue(v) for k,v in keyValues.items())

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
            if self._keyable:
                self.validateKeyValues(value)
            else:
                self.validateValue(value)
        except ValueError:
            return False
        return True
    
    @property
    def validators(self):
        return self._validators
    
    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    # isExpression:
    #   The default value of the attribute's descriptor is a static string expression that should be evaluated at runtime.
    #   This property only makes sense for output attributes.
    isExpression = Property(bool, lambda self: self._isExpression, constant=True)
    # isDynamicValue
    #   The default value of the attribute's descriptor is None, so it is not an input value,
    #   but an output value that is computed during the Node's process execution.
    isDynamicValue = Property(bool, lambda self: self._isDynamicValue, constant=True)
    # keyable:
    #   Whether the attribute can have a distinct value per key.
    #   By default, atribute value is not keyable.
    keyable = Property(bool, lambda self: self._keyable, constant=True)
    # keyType:
    #   The type of key corresponding to the attribute value.
    #   This property only makes sense for keyable attributes.
    keyType = Property(str, lambda self: self._keyType, constant=True)
    commandLineGroup = Property(str, lambda self: self._commandLineGroup, constant=True)
    advanced = Property(bool, lambda self: self._advanced, constant=True)
    enabled = Property(Variant, lambda self: self._enabled, constant=True)
    invalidate = Property(Variant, lambda self: self._invalidate, constant=True)
    semantic = Property(str, lambda self: self._semantic, constant=True)
    uidIgnoreValue = Property(Variant, lambda self: self._uidIgnoreValue, constant=True)
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
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, elementDesc, name, label=None, description=None, group="allParams", commandLineGroup=_setParamSentinel, 
                 advanced=False, semantic="", enabled=True, joinChar=" ", visible=True, exposed=False, value=None, validators=None):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        :param value: default value. Use None to declare a dynamic output ListAttribute
                      whose content is set during processChunk.
        """
        self._elementDesc = elementDesc
        self._joinChar = joinChar
        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group
        
        super(ListAttribute, self).__init__(name=name, label=label, description=description, value=value,
                                            invalidate=False, commandLineGroup=commandLineGroup, advanced=advanced, semantic=semantic,
                                            enabled=enabled, visible=visible, exposed=exposed, validators=validators)

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
            raise ValueError(f"ListAttribute only supports list/tuple input values "
                             f"(param: {self.name}, value: {value}, type: {type(value)})")
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
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, items, name, label=None, description=None, group="allParams", commandLineGroup=_setParamSentinel, 
                 advanced=False, semantic="",  enabled=True, joinChar=" ", brackets=None, visible=True,
                 exposed=False, validators=None):
        """
        :param items: the description of the Attributes composing this group
        """
        self._items = items
        self._joinChar = joinChar
        self._brackets = brackets
        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(GroupAttribute, self).__init__(name=name, label=label, description=description, value={},
                                             commandLineGroup=commandLineGroup, advanced=advanced, invalidate=False, semantic=semantic,
                                             enabled=enabled, visible=visible, exposed=exposed, validators=validators)

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
            # invalidKeys = set(value.keys()).difference([attr.name for attr in self._items])
            # if invalidKeys:
            #     raise ValueError(f"Value contains key that does not match group description: "
            #                      f"{invalidKeys}")
            if self._items and value.keys():
                commonKeys = set(value.keys()).intersection([attr.name for attr in self._items])
                if not commonKeys:
                    raise ValueError(f"Value contains no key that matches with the group "
                                     f"description (name={self.name}, values={value.keys()}, "
                                     f"desc={[attr.name for attr in self._items]})")
        elif isinstance(value, (list, tuple, set)):
            if len(value) != len(self._items):
                raise ValueError(f"Value contains incoherent number of values: "
                                 f"desc size: {len(self._items)}, value size: {len(value)}")
        else:
            raise ValueError(f"GroupAttribute only supports dict/list/tuple input values "
                             f"(param: {self.name}, value: {value}, type: {type(value)})")

        return value

    def checkValueTypes(self):
        """ Check the default value's and range's (if available) type of every attribute contained in the group
        (including nested attributes).

        Returns an empty string if all the attributes' types are valid, or concatenates the names of the attributes in
        the group with invalid types.
        """
        invalidParams = []
        for attr in self.items:
            name, error = attr.checkValueTypes()
            if name:
                invalidParams.append(name)
        if invalidParams:
            # In group "group", if parameters "x" and "y" (with "y" in nested group "subgroup") are invalid, the
            # returned string will be: "group:x, group:subgroup:y"
            return self.name + ":" + str(", " + self.name + ":").join(invalidParams), error
        return "", ValueTypeErrors.NONE

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
        attrMap = {attr.name: attr for attr in self._items}

        matchCount = 0
        for k, v in value.items():
            # each child value must match corresponding child attribute description
            if k in attrMap and attrMap[k].matchDescription(v, strict):
                matchCount += 1

        if strict:
            return matchCount == len(value.items()) == len(self._items)

        return matchCount > 0

    def retrieveChildrenInvalidations(self):
        allInvalidations = []
        for desc in self._items:
            allInvalidations.append(desc.invalidate)
        return allInvalidations

    items = Property(Variant, lambda self: self._items, constant=True)
    invalidate = Property(Variant, retrieveChildrenInvalidations, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)
    brackets = Property(str, lambda self: self._brackets, constant=True)


class Param(Attribute):
    """
    """
    def __init__(self, name, label, description, value, commandLineGroup, advanced, semantic, enabled,
                 keyable=False, keyType=None, invalidate=True, uidIgnoreValue=None, visible=True, exposed=False, validators=None):
        super(Param, self).__init__(name=name, label=label, description=description, value=value,
                                    keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup, advanced=advanced,
                                    enabled=enabled, invalidate=invalidate, semantic=semantic,
                                    uidIgnoreValue=uidIgnoreValue, visible=visible, exposed=exposed, validators=validators)


class File(Attribute):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, group="allParams", commandLineGroup=_setParamSentinel,
                 advanced=False, invalidate=True, semantic="", enabled=True, visible=True, exposed=True, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(File, self).__init__(name=name, label=label, description=description, value=value,
                                   commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
                                   invalidate=invalidate, semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError(f"File only supports string input (param: {self.name}, value: "
                             f"{value}, type: {type(value)})")
        return os.path.normpath(value).replace("\\", "/") if value else ""

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        # Some File values are functions generating a string: check whether the value is a string or if it
        # is a function (but there is no way to check that the function's output is indeed a string)
        if not isinstance(self.value, str) and not callable(self.value):
            return self.name, ValueTypeErrors.TYPE
        return "", ValueTypeErrors.NONE


class BoolParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, keyable=False, keyType=None,
                 group="allParams", commandLineGroup=_setParamSentinel, advanced=False,
                 enabled=True, invalidate=True, semantic="", visible=True, exposed=False, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(BoolParam, self).__init__(name=name, label=label, description=description, value=value,
                                        keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup,
                                        advanced=advanced, enabled=enabled, invalidate=invalidate,
                                        semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._valueType = bool

    def validateValue(self, value):
        if value is None:
            return value
        try:
            if isinstance(value, str):
                return bool(strtobool(value))
            return bool(value)
        except Exception:
            raise ValueError(f"BoolParam only supports bool value (param: {self.name}, "
                             f"value: {value}, type: {type(value)})")

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        if not isinstance(self.value, bool):
            return self.name, ValueTypeErrors.TYPE
        return "", ValueTypeErrors.NONE


class IntParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, range=None, keyable=False, keyType=None,
                 group="allParams", commandLineGroup=_setParamSentinel, advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False, validators=None):
        self._range = range

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(IntParam, self).__init__(name=name, label=label, description=description, value=value,
                                       keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup,
                                       advanced=advanced, enabled=enabled, invalidate=invalidate,
                                       semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._valueType = int

    def validateValue(self, value):
        if value is None:
            return value
        # Handle unsigned int values that are translated to int by shiboken and may overflow
        try:
            return int(value)
        except Exception:
            raise ValueError(f"IntParam only supports int value (param: {self.name}, value: "
                             f"{value}, type: {type(value)})")

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        if not isinstance(self.value, int):
            return self.name, ValueTypeErrors.TYPE
        if (self.range and not all([isinstance(r, int) for r in self.range])):
            return self.name, ValueTypeErrors.RANGE
        return "", ValueTypeErrors.NONE

    range = Property(VariantList, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, range=None, keyable=False, keyType=None,
                 group="allParams", commandLineGroup=_setParamSentinel, advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False, validators=None):
        self._range = range
        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(FloatParam, self).__init__(name=name, label=label, description=description, value=value,
                                         keyable=keyable, keyType=keyType, commandLineGroup=commandLineGroup,
                                         advanced=advanced, enabled=enabled, invalidate=invalidate,
                                         semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._valueType = float

    def validateValue(self, value):
        if value is None:
            return value
        try:
            return float(value)
        except Exception:
            raise ValueError(f"FloatParam only supports float value (param: {self.name}, value: "
                             f"{value}, type:{type(value)})")

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        if not isinstance(self.value, float):
            return self.name, ValueTypeErrors.TYPE
        if (self.range and not all([isinstance(r, float) for r in self.range])):
            return self.name, ValueTypeErrors.RANGE
        return "", ValueTypeErrors.NONE

    range = Property(VariantList, lambda self: self._range, constant=True)


class PushButtonParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, group="allParams", commandLineGroup=_setParamSentinel,
                 advanced=False, enabled=True, invalidate=True, semantic="", visible=True, exposed=False, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(PushButtonParam, self).__init__(name=name, label=label, description=description, value=None,
                                              commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
                                              invalidate=invalidate, semantic=semantic, visible=visible,
                                              exposed=exposed, validators=validators)
        self._valueType = None

    def getInstanceType(self):
        # Import within the method to prevent cyclic dependencies
        from meshroom.core.attribute import PushButtonParam
        return PushButtonParam

    def validateValue(self, value):
        return value

    def checkValueTypes(self):
        return "", ValueTypeErrors.NONE


class ChoiceParam(Param):
    """
    ChoiceParam is an Attribute that allows to choose a value among a list of possible values.

    When using `exclusive=True`, the value is a single element of the list of possible values.
    When using `exclusive=False`, the value is a list of elements of the list of possible values.

    Despite this being the standard behavior, ChoiceParam also supports custom value: it is possible to set any value,
    even outside list of possible values.

    The list of possible values on a ChoiceParam instance can be overriden at runtime.
    If those changes needs to be persisted, `saveValuesOverride` should be set to True.
    """

    # Keys for values override serialization schema (saveValuesOverride=True).
    _OVERRIDE_SERIALIZATION_KEY_VALUE = "__ChoiceParam_value__"
    _OVERRIDE_SERIALIZATION_KEY_VALUES = "__ChoiceParam_values__"

    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name: str, label=None, description=None, value=None, values=None, exclusive=True, saveValuesOverride=False,
                 group="allParams", commandLineGroup=_setParamSentinel, joinChar=" ", advanced=False, enabled=True,
                 invalidate=True, semantic="", visible=True, exposed=False, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(ChoiceParam, self).__init__(name=name, label=label, description=description, value=value,
                                          commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
                                          invalidate=invalidate, semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._values = values if values is not None else []
        self._saveValuesOverride = saveValuesOverride
        self._exclusive = exclusive
        self._joinChar = joinChar
        if self._values:
            # Look at the type of the first element of the possible values
            self._valueType = type(self._values[0])
        elif not exclusive and self._value is not None:
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

        serializedWithValuesOverride = isinstance(value, dict)
        if serializedWithValuesOverride:
            value = value[ChoiceParam._OVERRIDE_SERIALIZATION_KEY_VALUE]

        if self.exclusive:
            return self.conformValue(value)

        if isinstance(value, str):
            value = value.split(',')

        if not isinstance(value, Iterable):
            raise ValueError(f"Non-exclusive ChoiceParam value should be iterable (param: "
                             f"{self.name}, value: {value}, type: {type(value)}).")

        return [self.conformValue(v) for v in value]

    def checkValueTypes(self):
        # Check that the values have been provided as a list
        if not isinstance(self._values, list):
            return self.name, ValueTypeErrors.TYPE

        # None value is valid (dynamic default)
        if self._value is None:
            return "", ValueTypeErrors.NONE

        # If the choices are not exclusive, check that 'value' is a list, and check that it does not contain values that
        # are not available
        elif not self.exclusive and (not isinstance(self._value, list) or
                                     not all(val in self._values for val in self._value)):
            return self.name, ValueTypeErrors.RANGE

        # If the choices are exclusive, the value should NOT be a list but it can contain any value that is not in the
        # list of possible ones
        elif self.exclusive and isinstance(self._value, list):
            return self.name, ValueTypeErrors.TYPE

        return "", ValueTypeErrors.NONE

    values = Property(VariantList, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, group="allParams", commandLineGroup=_setParamSentinel,
                 advanced=False, enabled=True, invalidate=True, semantic="", uidIgnoreValue=None, visible=True, exposed=False, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(StringParam, self).__init__(name=name, label=label, description=description, value=value,
                                          commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
                                          invalidate=invalidate, semantic=semantic, uidIgnoreValue=uidIgnoreValue, visible=visible,
                                          exposed=exposed, validators=validators)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str):
            raise ValueError(f"StringParam value should be a string (param: "
                             f"{self.name}, value: {value}, type: {type(value)})")
        return value

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        if not isinstance(self.value, str):
            return self.name, ValueTypeErrors.TYPE
        return "", ValueTypeErrors.NONE


class ColorParam(Param):
    """
    """
    @deprecated.depreciateParam("group", "Param 'group' on {name} should not be used anymore. Please use 'commandLineGroup' instead")
    def __init__(self, name, label=None, description=None, value=None, group="allParams", commandLineGroup=_setParamSentinel,
                 advanced=False, enabled=True, invalidate=True, semantic="", visible=True, exposed=False, validators=None):

        commandLineGroup = commandLineGroup if commandLineGroup is not _setParamSentinel else group

        super(ColorParam, self).__init__(name=name, label=label, description=description, value=value,
                                         commandLineGroup=commandLineGroup, advanced=advanced, enabled=enabled,
                                         invalidate=invalidate, semantic=semantic, visible=visible, exposed=exposed, validators=validators)
        self._valueType = str

    def validateValue(self, value):
        if value is None:
            return value
        if not isinstance(value, str) or len(value.split(" ")) > 1:
            raise ValueError(f"ColorParam value should be a string containing either an SVG name "
                             f"or an hexadecimal color code (param: {self.name}, value: {value}, "
                             f"type: {type(value)})")
        return value

    def checkValueTypes(self):
        if self.value is None:
            return "", ValueTypeErrors.NONE
        if not isinstance(self.value, str):
            return self.name, ValueTypeErrors.TYPE
        return "", ValueTypeErrors.NONE
