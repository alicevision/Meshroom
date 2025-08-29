#!/usr/bin/env python
import copy
import os
import re
import weakref
import types
import logging

from collections.abc import Iterable, Sequence
from string import Template
from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, DictModel, Slot
from meshroom.core import desc, hashValue

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshroom.core.graph import Edge


def attributeFactory(description: str, value, isOutput: bool, node, root=None, parent=None):
    """
    Create an Attribute based on description type.

    Args:
        description: the Attribute description
        value: value of the Attribute. Will be set if not None.
        isOutput: whether the Attribute is an output attribute.
        node (Node): node owning the Attribute. Note that the created Attribute is not added to \
                     Node's attributes
        root: (optional) parent Attribute (must be ListAttribute or GroupAttribute)
        parent (BaseObject): (optional) the parent BaseObject if any
    """
    attr: Attribute = description.instanceType(node, description, isOutput, root, parent)
    if value is not None:
        attr._setValue(value)
    else:
        attr.resetToDefaultValue()

    # Only connect slot that reacts to value change once initial value has been set.
    # NOTE: This should be handled by the Node class, but we're currently limited by our core
    #       signal implementation that does not support emitting parameters.
    #       And using a lambda here to send the attribute as a parameter causes
    #       performance issues when using the pyside backend.
    attr.valueChanged.connect(attr._onValueChanged)

    return attr


class Attribute(BaseObject):
    """
    """
    LINK_EXPRESSION_REGEX =  re.compile(r'^\{[A-Za-z]+[A-Za-z0-9_.\[\]]*\}$')
    VALID_IMAGE_SEMANTICS = ["image", "imageList", "sequence"]
    VALID_3D_EXTENSIONS = [".obj", ".stl", ".fbx", ".gltf", ".abc", ".ply"]

    @staticmethod
    def isLinkExpression(value) -> bool:
        """
        Return whether the given argument is a link expression.
        A link expression is a string matching the {nodeName.attrName} pattern.
        """
        return isinstance(value, str) and Attribute.LINK_EXPRESSION_REGEX.match(value)

    def __init__(self, node, attributeDesc: desc.Attribute, isOutput: bool, root=None, parent=None):
        """
        Attribute constructor

        Args:
            node (Node): the Node hosting this Attribute
            attributeDesc: the description of this Attribute
            isOutput: whether this Attribute is an output of the Node
            root (Attribute): (optional) the root Attribute (List or Group) containing this one
            parent (BaseObject): (optional) the parent BaseObject
        """
        super().__init__(parent)
        self._root = None if root is None else weakref.ref(root)
        self._node = weakref.ref(node)
        self._desc: desc.Attribute = attributeDesc
        self._isOutput: bool = isOutput
        self._enabled: bool = True
        self._invalidate = False if self._isOutput else attributeDesc.invalidate

        # invalidation value for output attributes
        self._invalidationValue = ""

        self._value = None
        self.initValue()

    def _getFullName(self) -> str:
        """ 
        Get the attribute name following the path from the node to the attribute.
        Return: nodeName.groupName.subGroupName.name 
        """
        return f'{self.node.name}.{self._getRootName()}'
    
    def _getRootName(self) -> str:
        """ 
        Get the attribute name following the path from the node root to the attribute.
        Return: groupName.subGroupName.name 
        """
        if isinstance(self.root, ListAttribute):
            return f'{self.root.rootName}[{self.root.index(self)}]'
        elif isinstance(self.root, GroupAttribute):
            return f'{self.root.rootName}.{self._desc.name}'
        return self._desc.name

    def asLinkExpr(self) -> str:
        """ Return link expression for this Attribute """
        return "{" + self._getFullName() + "}"

    @Slot(str, result=bool)
    def matchText(self, text: str) -> bool:
        return self.fullLabel.lower().find(text.lower()) > -1

    def _getEnabled(self) -> bool:
        if isinstance(self._desc.enabled, types.FunctionType):
            try:
                return self._desc.enabled(self.node)
            except Exception:
                # Node implementation may fail due to version mismatch
                return True
        return self._desc.enabled

    def _setEnabled(self, v):
        if self._enabled == v:
            return
        self._enabled = v
        self.enabledChanged.emit()

    def _isValid(self):
        """
        Check attribute description validValue:
            - If it is a function, execute it and return the result
            - Otherwise, simply return true
        """
        if isinstance(self._desc.validValue, types.FunctionType):
            try:
                return self._desc.validValue(self.node)
            except Exception:
                return True
        return True

    def validateValue(self, value):
        return self._desc.validateValue(value)

    def _getValue(self):
        if self.isLink:
            return self._getDirectInputLink().value
        return self._value

    def _setValue(self, value):
        if self._value == value:
            return

        if isinstance(value, Attribute) or Attribute.isLinkExpression(value):
            # if we set a link to another attribute
            self._value = value
        elif isinstance(value, types.FunctionType):
            # evaluate the function
            self._value = value(self)
        else:
            # if we set a new value, we use the attribute descriptor validator to check the
            # validity of the value and apply some conversion if needed
            convertedValue = self.validateValue(value)
            self._value = convertedValue

        # Request graph update when input parameter value is set
        # and parent node belongs to a graph
        # Output attributes value are set internally during the update process,
        # which is why we don't trigger any update in this case
        # TODO: update only the nodes impacted by this change
        # TODO: only update the graph if this attribute participates to a UID
        if self.isInput:
            self.requestGraphUpdate()
            # TODO: only call update of the node if the attribute is internal
            # Internal attributes are set as inputs
            self.requestNodeUpdate()

        self.valueChanged.emit()

    @Slot()
    def _onValueChanged(self):
        self.node._onAttributeChanged(self)

    def upgradeValue(self, exportedValue):
        self._setValue(exportedValue)

    def initValue(self):
        if self._desc._valueType is not None:
            self._value = self._desc._valueType()

    def resetToDefaultValue(self):
        self._setValue(copy.copy(self.defaultValue()))

    def requestGraphUpdate(self):
        if self.node.graph:
            self.node.graph.markNodesDirty(self.node)
            self.node.graph.update()

    def requestNodeUpdate(self):
        # Update specific node information that do not affect the rest of the graph
        # (like internal attributes)
        if self.node:
            self.node.updateInternalAttributes()

    def uid(self) -> str:
        """
        Compute the UID for the attribute.
        """
        if self.isOutput:
            if self._desc.isDynamicValue:
                # If the attribute is a dynamic output, the UID is derived from the node UID.
                # To guarantee that each output attribute receives a unique ID, we add the attribute
                # name to it.
                return hashValue((self.name, self.node._uid))
            else:
                # Only dependent on the hash of its value without the cache folder.
                # "/" at the end of the link is stripped to prevent having different UIDs depending
                # on whether the invalidation value finishes with it or not
                strippedInvalidationValue = self._invalidationValue.rstrip("/")
                return hashValue(strippedInvalidationValue)
        if self.isLink:
            linkRootAttribute = self._getDirectInputLink(recursive=True)
            return linkRootAttribute.uid()
        if isinstance(self._value, (list, tuple, set,)):
            # non-exclusive choice param
            # hash of sorted values hashed
            return hashValue([hashValue(v) for v in sorted(self._value)])
        return hashValue(self._value)

    def _applyExpr(self):
        """
        For string parameters with an expression (when loaded from file),
        this function convert the expression into a real edge in the graph
        and clear the string value.
        """
        v = self._value
        g = self.node.graph
        if not g:
            return
        if isinstance(v, Attribute):
            g.addEdge(v, self)
            self.resetToDefaultValue()
        elif self.isInput and Attribute.isLinkExpression(v):
            # value is a link to another attribute
            link = v[1:-1]
            linkNodeName, linkAttrName = link.split('.')
            try:
                node = g.node(linkNodeName)
                if not node:
                    raise KeyError(f"Node '{linkNodeName}' not found")
                g.addEdge(node.attribute(linkAttrName), self)
            except KeyError as err:
                logging.warning('Connect Attribute from Expression failed.')
                logging.warning(f'Expression: "{v}"\nError: "{err}".')
            self.resetToDefaultValue()

    def getExportValue(self):
        if self.isLink:
            return self._getDirectInputLink().asLinkExpr()
        if self.isOutput and self._desc.isExpression:
            return self.defaultValue()
        return self.value

    def _getEvalValue(self):
        """
        Return the value. If it is a string, expressions will be evaluated.
        """
        if isinstance(self.value, str):
            env = self.node.nodePlugin.configFullEnv if self.node.nodePlugin else os.environ
            substituted = Template(self.value).safe_substitute(env)
            try:
                varResolved = substituted.format(**self.node._cmdVars)
                return varResolved
            except (KeyError, IndexError):
                # Catch KeyErrors and IndexErros to be able to open files created prior to the
                # support of relative variables (when self.node._cmdVars was not used to evaluate
                # expressions in the attribute)
                return substituted
        return self.value

    def getValueStr(self, withQuotes=True) -> str:
        """
        Return the value formatted as a string with quotes to deal with spaces.
        If it is a string, expressions will be evaluated.
        If it is an empty string, it will returns 2 quotes.
        If it is an empty list, it will returns a really empty string.
        If it is a list with one empty string element, it will returns 2 quotes.
        """
        # ChoiceParam with multiple values should be combined
        if isinstance(self._desc, desc.ChoiceParam) and not self._desc.exclusive:
            # Ensure value is a list as expected
            assert (isinstance(self.value, Sequence) and not isinstance(self.value, str))
            v = self._desc.joinChar.join(self._getEvalValue())
            if withQuotes and v:
                return f'"{v}"'
            return v
        # String, File, single value Choice are based on strings and should includes quotes
        # to deal with spaces
        if withQuotes and isinstance(self._desc, (desc.StringParam, desc.File, desc.ChoiceParam)):
            return f'"{self._getEvalValue()}"'
        return str(self._getEvalValue())

    def defaultValue(self):
        if isinstance(self._desc.value, types.FunctionType):
            try:
                return self._desc.value(self)
            except Exception as e:
                if not self.node.isCompatibilityNode:
                    # Log message only if we are not in compatibility mode
                    logging.warning("Failed to evaluate default value (node lambda) for attribute '{}': {}".
                                    format(self.name, e))
                return None
        # Need to force a copy, for the case where the value is a list
        # (avoid reference to the desc value)
        return copy.copy(self._desc.value)

    def _isDefault(self) -> bool:
        return self.value == self.defaultValue()

    def getPrimitiveValue(self, exportDefault=True):
        return self._value

    def updateInternals(self):
        # Emit if the enable status has changed
        self._setEnabled(self._getEnabled())

    def _is2D(self) -> bool:
        """ Return True if the current attribute is considered as a 2d file """
        if not self._desc.semantic:
            return False

        return next((imageSemantic for imageSemantic in Attribute.VALID_IMAGE_SEMANTICS
                     if self._desc.semantic == imageSemantic), None) is not None

    def _is3D(self) -> bool:
        """ Return True if the current attribute is considered as a 3d file """
        if self._desc.semantic == "3d":
            return True

        # If the attribute is a File attribute, it is an instance of str and can be iterated over
        hasSupportedExt = isinstance(self.value, str) and any(ext in self.value for ext in Attribute.VALID_3D_EXTENSIONS)
        if hasSupportedExt:
            return True

        return False
    
    def _isLink(self) -> bool:
        """ 
        Whether the attribute is a link to another attribute. 
        """
        return self.node.graph and self.isInput and self.node.graph._edges and \
            self in self.node.graph._edges.keys()
  
    def _getDirectInputLink(self, recursive=False) -> "Attribute":
        """ 
        Return the direct upstream connected attribute.
        :param recursive: recursive call, return the root attribute
        """
        if not self.isLink:
            return None
        linkAttribute = self.node.graph.edge(self).src
        if recursive and linkAttribute.isLink:
            return linkAttribute._getDirectInputLink(recursive)
        return linkAttribute

    def _getDirectOutputLinks(self) -> list["Attribute"]:
        """ 
        Return the list of direct downstream connected attributes.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return []
        return [edge.dst for edge in self.node.graph.edges.values() if edge.src == self]
    
    def _getAllInputLinks(self) -> list["Attribute"]:
        """ 
        Return the list of upstream connected attributes for the attribute or any of its elements.
        """
        directInputLink = self._getDirectInputLink()
        if directInputLink is None: 
            return []
        return [directInputLink]

    def _getAllOutputLinks(self) -> list["Attribute"]:
        """ 
        Return the list of downstream connected attributes for the attribute or any of its elements.
        """
        return self._getDirectOutputLinks()

    def _hasAnyInputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is a link to another attribute.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False
        return next((edge for edge in self.node.graph.edges.values() if edge.src == self), None) is not None

    def _hasAnyOutputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is linked by another attribute.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False
        return next((edge for edge in self.node.graph.edges.values() if edge.src == self), None) is not None
    
    
    # Properties and signals 

    node = Property(BaseObject, lambda self: self._node(), constant=True)
    root = Property(BaseObject, lambda self: self._root() if self._root else None, constant=True)

    fullName = Property(str, _getFullName, constant=True)
    rootName = Property(str, _getRootName, constant=True)
    desc = Property(desc.Attribute, lambda self: self._desc, constant=True)
    name = Property(str, lambda self: self._desc._name, constant=True)
    label = Property(str, lambda self: self._desc.label, constant=True)
    type = Property(str, lambda self: self._desc.type, constant=True)
    baseType = Property(str, lambda self: self._desc.type, constant=True)
    isInput = Property(bool, lambda self: not self._isOutput, constant=True)
    isOutput = Property(bool, lambda self: self._isOutput, constant=True)
    isReadOnly = Property(bool, lambda self: not self._isOutput and self.node.isCompatibilityNode, constant=True)

    enabledChanged = Signal()
    enabled = Property(bool, _getEnabled, _setEnabled, notify=enabledChanged)
    invalidate = Property(bool, lambda self: self._invalidate, constant=True)

    valueChanged = Signal()
    value = Property(Variant, _getValue, _setValue, notify=valueChanged)
    evalValue = Property(Variant, _getEvalValue, notify=valueChanged)
    isDefault = Property(bool, _isDefault, notify=valueChanged)
    isValid = Property(bool, _isValid, notify=valueChanged)
    is2D = Property(bool, _is2D, constant=True)
    is3D = Property(bool, _is3D, constant=True)
    

    # Attribute link properties and signals

    inputLinksChanged = Signal()
    outputLinksChanged = Signal()

    # isLink:
    # Whether the attribute is a direct link to another attribute.
    isLink = Property(bool, _isLink, notify=inputLinksChanged)
    # directInputRootLink:
    #   The direct upstream connected root attribute.
    directInputRootLink = Property(Variant, lambda self: self._getDirectInputLink(recursive=True), notify=inputLinksChanged)
    # directInputLink:
    #   The direct upstream connected attribute.
    directInputLink = Property(BaseObject, _getDirectInputLink, notify=inputLinksChanged)
    # directOutputLinks:
    #   The list of direct downstream connected attributes.
    directOutputLinks = Property(Variant, _getDirectOutputLinks, notify=outputLinksChanged)
    # allInputLinks:
    #   The list of upstream connected attributes for the attribute or any of its elements.
    allInputLinks = Property(Variant, _getAllInputLinks, notify=inputLinksChanged)
    # allOutputLinks:
    #   The list of downstream connected attributes for the attribute or any of its elements.
    allOutputLinks = Property(Variant, _getAllOutputLinks, notify=outputLinksChanged)
    # hasAnyInputLinks:
    #   Whether the attribute or any of its elements is a link to another attribute.
    hasAnyInputLinks = Property(bool, _hasAnyInputLinks, notify=inputLinksChanged)
    # hasAnyOutputLinks:
    #   Whether the attribute or any of its elements is linked by another attribute.
    hasAnyOutputLinks = Property(bool, _hasAnyOutputLinks, notify=outputLinksChanged)

def raiseIfLink(func):
    """ If Attribute instance is a link, raise a RuntimeError. """
    def wrapper(attr, *args, **kwargs):
        if attr.isLink:
            raise RuntimeError("Can't modify connected Attribute")
        return func(attr, *args, **kwargs)
    return wrapper


class PushButtonParam(Attribute):
    def __init__(self, node, attributeDesc: desc.PushButtonParam, isOutput: bool,
                 root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)

    @Slot()
    def clicked(self):
        self.node.onAttributeClicked(self)


class ChoiceParam(Attribute):

    def __init__(self, node, attributeDesc: desc.ChoiceParam, isOutput: bool,
                 root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)
        self._values = None

    def __len__(self):
        return len(self.getValues())

    def getValues(self):
        if (linkParam := self._getDirectInputLink()) is not None:
            return linkParam.getValues()
        return self._values if self._values is not None else self._desc._values

    def conformValue(self, val):
        """ Conform 'val' to the correct type and check for its validity """
        return self._desc.conformValue(val)

    def validateValue(self, value):
        if self._desc.exclusive:
            return self.conformValue(value)

        if isinstance(value, str):
            value = value.split(',')

        if not isinstance(value, Iterable):
            raise ValueError("Non exclusive ChoiceParam value should be iterable (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))
        return [self.conformValue(v) for v in value]

    def _setValue(self, value):
        # Handle alternative serialization for ChoiceParam with overriden values.
        serializedValueWithValuesOverrides = isinstance(value, dict)
        if serializedValueWithValuesOverrides:
            super()._setValue(value[self._desc._OVERRIDE_SERIALIZATION_KEY_VALUE])
            self.setValues(value[self._desc._OVERRIDE_SERIALIZATION_KEY_VALUES])
        else:
            super()._setValue(value)

    def setValues(self, values):
        if values == self._values:
            return
        self._values = values
        self.valuesChanged.emit()

    def getExportValue(self):
        useStandardSerialization = self.isLink or not self._desc._saveValuesOverride or \
            self._values is None

        if useStandardSerialization:
            return super().getExportValue()

        return {
            self._desc._OVERRIDE_SERIALIZATION_KEY_VALUE: self._value,
            self._desc._OVERRIDE_SERIALIZATION_KEY_VALUES: self._values,
        }

    value = Property(Variant, Attribute._getValue, _setValue, notify=Attribute.valueChanged)
    valuesChanged = Signal()
    values = Property(Variant, getValues, setValues, notify=valuesChanged)


class ListAttribute(Attribute):

    def __init__(self, node, attributeDesc: desc.ListAttribute, isOutput: bool,
                 root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)

    def __len__(self):
        if self.value is None:
            return 0
        return len(self.value)

    def __iter__(self):
        return iter(self.value)

    def at(self, idx):
        """ Returns child attribute at index 'idx'. """
        # Implement 'at' rather than '__getitem__'
        # since the later is called spuriously when object is used in QML
        return self.value.at(idx)

    def index(self, item):
        return self.value.indexOf(item)

    def initValue(self):
        self.resetToDefaultValue()

    def resetToDefaultValue(self):
        self._value = ListModel(parent=self)
        self.valueChanged.emit()

    def _setValue(self, value):
        if self.node.graph:
            self.remove(0, len(self))
        # Link to another attribute
        if isinstance(value, ListAttribute) or Attribute.isLinkExpression(value):
            self._value = value
        # New value
        else:
            # During initialization self._value may not be set
            if self._value is None:
                self._value = ListModel(parent=self)
            newValue = self._desc.validateValue(value)
            self.extend(newValue)
        self.requestGraphUpdate()

    def upgradeValue(self, exportedValues):
        if not isinstance(exportedValues, list):
            if isinstance(exportedValues, ListAttribute) or \
               Attribute.isLinkExpression(exportedValues):
                self._setValue(exportedValues)
                return
            raise RuntimeError("ListAttribute.upgradeValue: the given value is of type " +
                               str(type(exportedValues)) + " but a 'list' is expected.")

        attrs = []
        for v in exportedValues:
            a = attributeFactory(self._desc.elementDesc, None, self.isOutput,
                                 self.node, self)
            a.upgradeValue(v)
            attrs.append(a)
        index = len(self._value)
        self._value.insert(index, attrs)
        self.valueChanged.emit()
        self._applyExpr()
        self.requestGraphUpdate()

    @raiseIfLink
    def append(self, value):
        self.extend([value])

    @raiseIfLink
    def insert(self, index, value):
        if self._value is None:
            self._value = ListModel(parent=self)
        values = value if isinstance(value, list) else [value]
        attrs = [attributeFactory(self._desc.elementDesc, v, self.isOutput, self.node, self)
                 for v in values]
        self._value.insert(index, attrs)
        self.valueChanged.emit()
        self._applyExpr()
        self.requestGraphUpdate()

    @raiseIfLink
    def extend(self, values):
        self.insert(len(self), values)

    @raiseIfLink
    def remove(self, index, count=1):
        if self._value is None:
            return
        if self.node.graph:
            from meshroom.core.graph import GraphModification
            with GraphModification(self.node.graph):
                # remove potential links
                for i in range(index, index + count):
                    attr = self._value.at(i)
                    if attr.isLink:
                        # delete edge if the attribute is linked
                        self.node.graph.removeEdge(attr)
        self._value.removeAt(index, count)
        self.requestGraphUpdate()
        self.valueChanged.emit()

    def uid(self):
        if isinstance(self.value, ListModel):
            uids = []
            for value in self.value:
                if value.invalidate:
                    uids.append(value.uid())
            return hashValue(uids)
        return super().uid()

    def _applyExpr(self):
        if not self.node.graph:
            return
        if isinstance(self._value, ListAttribute) or Attribute.isLinkExpression(self._value):
            super()._applyExpr()
        else:
            for value in self._value:
                value._applyExpr()

    def getExportValue(self):
        if self.isLink:
            return self._getDirectInputLink().asLinkExpr()
        return [attr.getExportValue() for attr in self._value]

    def defaultValue(self) -> list:
        return []

    def _isDefault(self) -> bool:
        return len(self._value) == 0

    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value]
        return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value
                if not attr.isDefault]

    def getValueStr(self, withQuotes=True) -> str:
        assert isinstance(self.value, ListModel)
        if self._desc.joinChar == ' ':
            return self._desc.joinChar.join([v.getValueStr(withQuotes=withQuotes)
                                                     for v in self.value])
        v = self._desc.joinChar.join([v.getValueStr(withQuotes=False)
                                              for v in self.value])
        if withQuotes and v:
            return f'"{v}"'
        return v

    def updateInternals(self):
        super().updateInternals()
        for attr in self._value:
            attr.updateInternals()
    
    # Override
    def _getAllInputLinks(self) -> list["Attribute"]:
        """ 
        Return the list of upstream connected attributes for the attribute or any of its elements."
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return []
        return [edge.src for edge in self.node.graph.edges.values() if edge.dst == self or edge.dst in self._value]

    # Override
    def _getAllOutputLinks(self) -> list["Attribute"]:
        """ 
        Return the list of downstream connected attributes for the attribute or any of its elements."
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return []
        return [edge.dst for edge in self.node.graph.edges.values() if edge.src == self or edge.src in self._value]
    
    # Override
    def _hasAnyInputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is a link to another attribute.
        """
        return super()._hasAnyInputLinks() or \
               any(attribute.hasAnyInputLinks for attribute in self._value if hasattr(attribute, 'hasAnyInputLinks'))

    # Override
    def _hasAnyOutputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is linked by another attribute.
        """
        return super()._hasAnyOutputLinks() or \
               any(attribute.hasAnyOutputLinks for attribute in self._value if hasattr(attribute, 'hasAnyOutputLinks'))
            

    # Override value property setter
    value = Property(Variant, Attribute._getValue, _setValue, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)
    baseType = Property(str, lambda self: self._desc.elementDesc.__class__.__name__, constant=True)

    # Override attribute link properties
    allInputLinks = Property(Variant, _getAllInputLinks, notify=Attribute.inputLinksChanged)
    allOutputLinks = Property(Variant, _getAllOutputLinks, notify=Attribute.outputLinksChanged)
    hasAnyInputLinks = Property(bool, _hasAnyInputLinks, notify=Attribute.inputLinksChanged)
    hasAnyOutputLinks = Property(bool, _hasAnyOutputLinks, notify=Attribute.outputLinksChanged)


class GroupAttribute(Attribute):

    def __init__(self, node, attributeDesc: desc.GroupAttribute, isOutput: bool,
                 root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)

    def __getattr__(self, key):
        try:
            return super().__getattr__(key)
        except AttributeError:
            try:
                return self._value.get(key)
            except KeyError:
                raise AttributeError(key)

    def _setValue(self, exportedValue):
        value = self.validateValue(exportedValue)
        if isinstance(value, dict):
            # set individual child attribute values
            for key, v in value.items():
                self._value.get(key).value = v
        elif isinstance(value, (list, tuple)):
            if len(self._desc._groupDesc) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self._desc._groupDesc, value):
                self._value.get(attrDesc.name).value = v
        else:
            raise AttributeError(f"Failed to set on GroupAttribute: {str(value)}")

    def upgradeValue(self, exportedValue):
        value = self.validateValue(exportedValue)
        if isinstance(value, dict):
            # set individual child attribute values
            for key, v in value.items():
                if key in self._value.keys():
                    self._value.get(key).upgradeValue(v)
        elif isinstance(value, (list, tuple)):
            if len(self._desc._groupDesc) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self._desc._groupDesc, value):
                self._value.get(attrDesc.name).upgradeValue(v)
        else:
            raise AttributeError(f"Failed to set on GroupAttribute: {str(value)}")

    def initValue(self):
        self._value = DictModel(keyAttrName='name', parent=self)
        subAttributes = []
        for subAttrDesc in self._desc.groupDesc:
            childAttr = attributeFactory(subAttrDesc, None, self.isOutput, self.node, self)
            subAttributes.append(childAttr)
            childAttr.valueChanged.connect(self.valueChanged)
        self._value.reset(subAttributes)

    def resetToDefaultValue(self):
        for attrDesc in self._desc._groupDesc:
            self._value.get(attrDesc.name).resetToDefaultValue()

    @Slot(str, result=Attribute)
    def childAttribute(self, key: str) -> Attribute:
        """
        Get child attribute by name or None if none was found.

        Args:
            key: the name of the child attribute

        Returns:
            Attribute: the child attribute or None
        """
        try:
            return self._value.get(key)
        except KeyError:
            return None

    def uid(self):
        uids = []
        for k, v in self._value.items():
            if v.enabled and v.invalidate:
                uids.append(v.uid())
        return hashValue(uids)

    def _applyExpr(self):
        for value in self._value:
            value._applyExpr()

    def getExportValue(self):
        return {key: attr.getExportValue() for key, attr in self._value.objects.items()}

    def _isDefault(self):
        return all(v.isDefault for v in self._value)

    def defaultValue(self):
        return {key: attr.defaultValue() for key, attr in self._value.items()}

    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items()}
        return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items()
                if not attr.isDefault}

    def getValueStr(self, withQuotes=True):
        # add brackets if requested
        strBegin = ''
        strEnd = ''
        if self._desc.brackets is not None:
            if len(self._desc.brackets) == 2:
                strBegin = self._desc.brackets[0]
                strEnd = self._desc.brackets[1]
            else:
                raise AttributeError(f"Incorrect brackets on GroupAttribute: {self._desc.brackets}")

        # particular case when using space separator
        spaceSep = self._desc.joinChar == ' '

        # sort values based on child attributes group description order
        sortedSubValues = [self._value.get(attr.name).getValueStr(withQuotes=spaceSep)
                           for attr in self._desc.groupDesc]
        s = self._desc.joinChar.join(sortedSubValues)

        if withQuotes and not spaceSep:
            return f'"{strBegin}{s}{strEnd}"'
        return f'{strBegin}{s}{strEnd}'

    def updateInternals(self):
        super().updateInternals()
        for attr in self._value:
            attr.updateInternals()

    @Slot(str, result=bool)
    def matchText(self, text: str) -> bool:
        return super().matchText(text) or any(c.matchText(text) for c in self._value)

    # Override value property
    value = Property(Variant, Attribute._getValue, _setValue, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)
