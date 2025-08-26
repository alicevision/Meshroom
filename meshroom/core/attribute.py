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
        attr._set_value(value)
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
    stringIsLinkRe = re.compile(r'^\{[A-Za-z]+[A-Za-z0-9_.\[\]]*\}$')

    VALID_IMAGE_SEMANTICS = ["image", "imageList", "sequence"]
    VALID_3D_EXTENSIONS = [".obj", ".stl", ".fbx", ".gltf", ".abc", ".ply"]

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
        self._name: str = attributeDesc.name
        self._root = None if root is None else weakref.ref(root)
        self._node = weakref.ref(node)
        self.attributeDesc: desc.Attribute = attributeDesc
        self._isOutput: bool = isOutput
        self._label: str = attributeDesc.label
        self._enabled: bool = True
        self._validValue: bool = True
        self._description: str = attributeDesc.description
        self._invalidate = False if self._isOutput else attributeDesc.invalidate

        # invalidation value for output attributes
        self._invalidationValue = ""

        self._value = None
        self.initValue()

    @property
    def node(self):
        return self._node()

    @property
    def root(self):
        return self._root() if self._root else None

    def getName(self) -> str:
        """ Attribute name """
        return self._name

    def getFullName(self) -> str:
        """ Name inside the Graph: groupName.name """
        if isinstance(self.root, ListAttribute):
            return f'{self.root.getFullName()}[{self.root.index(self)}]'
        elif isinstance(self.root, GroupAttribute):
            return f'{self.root.getFullName()}.{self.getName()}'
        elif isinstance(self.root, MapAttribute):
            return f'{self.root.getFullName()}["{self.root.key(self)}"]'
        return self.getName()

    def getFullNameToNode(self) -> str:
        """ Name inside the Graph: nodeName.groupName.name """
        return f'{self.node.name}.{self.getFullName()}'

    def getFullNameToGraph(self) -> str:
        """ Name inside the Graph: graphName.nodeName.groupName.name """
        graphName = self.node.graph.name if self.node.graph else "UNDEFINED"
        return f'{graphName}.{self.getFullNameToNode()}'

    def asLinkExpr(self) -> str:
        """ Return link expression for this Attribute """
        return "{" + self.getFullNameToNode() + "}"

    def getType(self) -> str:
        return self.attributeDesc.type

    def _isReadOnly(self) -> bool:
        return not self._isOutput and self.node.isCompatibilityNode

    def getBaseType(self) -> str:
        return self.getType()

    def getLabel(self) -> str:
        return self._label

    @Slot(str, result=bool)
    def matchText(self, text: str) -> bool:
        return self.fullLabel.lower().find(text.lower()) > -1

    def getFullLabel(self) -> str:
        """
        Full Label includes the name of all parent groups, e.g. 'groupLabel subGroupLabel Label'.
        """
        if isinstance(self.root, ListAttribute):
            return self.root.getFullLabel()
        elif isinstance(self.root, GroupAttribute):
            return f'{self.root.getFullLabel()} {self.getLabel()}'
        return self.getLabel()

    def getFullLabelToNode(self) -> str:
        """ Label inside the Graph: nodeLabel groupLabel Label """
        return f'{self.node.label} {self.getFullLabel()}'

    def getFullLabelToGraph(self) -> str:
        """ Label inside the Graph: graphName nodeLabel groupLabel Label """
        graphName = self.node.graph.name if self.node.graph else "UNDEFINED"
        return f'{graphName} {self.getFullLabelToNode()}'

    def getEnabled(self) -> bool:
        if isinstance(self.desc.enabled, types.FunctionType):
            try:
                return self.desc.enabled(self.node)
            except Exception:
                # Node implementation may fail due to version mismatch
                return True
        return self.attributeDesc.enabled

    def setEnabled(self, v):
        if self._enabled == v:
            return
        self._enabled = v
        self.enabledChanged.emit()

    def getUidIgnoreValue(self):
        """ Value for which the attribute should be ignored during the UID computation. """
        return self.attributeDesc.uidIgnoreValue

    def getValidValue(self):
        """
        Get the status of _validValue:
            - If it is a function, execute it and return the result
            - Otherwise, simply return its value
        """
        if isinstance(self.desc.validValue, types.FunctionType):
            try:
                return self.desc.validValue(self.node)
            except Exception:
                return True
        return self._validValue

    def setValidValue(self, value):
        if self._validValue == value:
            return
        self._validValue = value

    def validateValue(self, value):
        return self.desc.validateValue(value)

    def _get_value(self):
        if self.isLink:
            return self.getLinkParam().value
        return self._value

    def _set_value(self, value):
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
        self.validValueChanged.emit()

    @Slot()
    def _onValueChanged(self):
        self.node._onAttributeChanged(self)

    def _set_label(self, label):
        if self._label == label:
            return
        self._label = label
        self.labelChanged.emit()

    def _get_description(self):
        return self._description

    def _set_description(self, desc):
        if self._description == desc:
            return
        self._description = desc
        self.descriptionChanged.emit()

    def upgradeValue(self, exportedValue):
        self._set_value(exportedValue)

    def initValue(self):
        if self.desc._valueType is not None:
            self._value = self.desc._valueType()

    def resetToDefaultValue(self):
        self._set_value(copy.copy(self.defaultValue()))

    def requestGraphUpdate(self):
        if self.node.graph:
            self.node.graph.markNodesDirty(self.node)
            self.node.graph.update()

    def requestNodeUpdate(self):
        # Update specific node information that do not affect the rest of the graph
        # (like internal attributes)
        if self.node:
            self.node.updateInternalAttributes()

    @property
    def isOutput(self) -> bool:
        return self._isOutput

    @property
    def isInput(self) -> bool:
        return not self._isOutput

    def uid(self) -> str:
        """
        Compute the UID for the attribute.
        """
        if self.isOutput:
            if self.desc.isDynamicValue:
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
            linkParam = self.getLinkParam(recursive=True)
            return linkParam.uid()
        if isinstance(self._value, (list, tuple, set,)):
            # non-exclusive choice param
            # hash of sorted values hashed
            return hashValue([hashValue(v) for v in sorted(self._value)])
        return hashValue(self._value)

    @property
    def isLink(self) -> bool:
        """ Whether the input attribute is a link to another attribute. """
        # note: directly use self.node.graph._edges to avoid using the property that may become
        # invalid at some point
        return self.node.graph and self.isInput and self.node.graph._edges and \
            self in self.node.graph._edges.keys()

    @staticmethod
    def isLinkExpression(value) -> bool:
        """
        Return whether the given argument is a link expression.
        A link expression is a string matching the {nodeName.attrName} pattern.
        """
        return isinstance(value, str) and Attribute.stringIsLinkRe.match(value)

    def getLinkParam(self, recursive=False):
        if not self.isLink:
            return None
        linkParam = self.node.graph.edge(self).src
        if not recursive:
            return linkParam
        if linkParam.isLink:
            return linkParam.getLinkParam(recursive)
        return linkParam

    @property
    def hasOutputConnections(self) -> bool:
        """
        Whether the attribute has output connections, i.e is the source of at least one edge.
        """
        # safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False
        return next((edge for edge in self.node.graph.edges.values() if edge.src == self), None) is not None

    def getInputConnections(self) -> list["Edge"]:
        """ Retrieve the upstreams connected edges """
        if not self.node.graph or not self.node.graph.edges:
            return []

        return [edge for edge in self.node.graph.edges.values() if edge.dst == self]

    def getOutputConnections(self) -> list["Edge"]:
        """ Retrieve all the edges connected to this attribute """
        if not self.node.graph or not self.node.graph.edges:
            return []

        return [edge for edge in self.node.graph.edges.values() if edge.src == self]

    def getLinkedInAttributes(self) -> list["Attribute"]:
        """ Return the upstreams connected attributes  """
        return [edge.src for edge in self.getInputConnections()]

    def getLinkedOutAttributes(self) -> list["Attribute"]:
        """ Return the downstreams connected attributes """
        return [edge.dst for edge in self.getOutputConnections()]

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
            return self.getLinkParam().asLinkExpr()
        if self.isOutput and self.desc.isExpression:
            return self.defaultValue()
        return self.value

    def getEvalValue(self):
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
        if isinstance(self.attributeDesc, desc.ChoiceParam) and not self.attributeDesc.exclusive:
            # Ensure value is a list as expected
            assert (isinstance(self.value, Sequence) and not isinstance(self.value, str))
            v = self.attributeDesc.joinChar.join(self.getEvalValue())
            if withQuotes and v:
                return f'"{v}"'
            return v
        # String, File, single value Choice are based on strings and should includes quotes
        # to deal with spaces
        if withQuotes and isinstance(self.attributeDesc,
                                     (desc.StringParam, desc.File, desc.ChoiceParam)):
            return f'"{self.getEvalValue()}"'
        return str(self.getEvalValue())

    def defaultValue(self):
        if isinstance(self.desc.value, types.FunctionType):
            try:
                return self.desc.value(self)
            except Exception as e:
                if not self.node.isCompatibilityNode:
                    # Log message only if we are not in compatibility mode
                    logging.warning("Failed to evaluate default value (node lambda) for attribute '{}': {}".
                                    format(self.name, e))
                return None
        # Need to force a copy, for the case where the value is a list
        # (avoid reference to the desc value)
        return copy.copy(self.desc.value)

    def _isDefault(self) -> bool:
        return self.value == self.defaultValue()

    def getPrimitiveValue(self, exportDefault=True):
        return self._value

    def updateInternals(self):
        # Emit if the enable status has changed
        self.setEnabled(self.getEnabled())

    def _is3D(self) -> bool:
        """ Return True if the current attribute is considered as a 3d file """
        if self.desc.semantic == "3d":
            return True

        # If the attribute is a File attribute, it is an instance of str and can be iterated over
        hasSupportedExt = isinstance(self.value, str) and any(ext in self.value for ext in Attribute.VALID_3D_EXTENSIONS)
        if hasSupportedExt:
            return True

        return False

    def _is2D(self) -> bool:
        """ Return True if the current attribute is considered as a 2d file """
        if not self.desc.semantic:
            return False

        return next((imageSemantic for imageSemantic in Attribute.VALID_IMAGE_SEMANTICS
                     if self.desc.semantic == imageSemantic), None) is not None

    name = Property(str, getName, constant=True)
    fullName = Property(str, getFullName, constant=True)
    fullNameToNode = Property(str, getFullNameToNode, constant=True)
    fullNameToGraph = Property(str, getFullNameToGraph, constant=True)
    labelChanged = Signal()
    label = Property(str, getLabel, _set_label, notify=labelChanged)
    fullLabel = Property(str, getFullLabel, constant=True)
    fullLabelToNode = Property(str, getFullLabelToNode, constant=True)
    fullLabelToGraph = Property(str, getFullLabelToGraph, constant=True)
    type = Property(str, getType, constant=True)
    baseType = Property(str, getType, constant=True)
    isReadOnly = Property(bool, _isReadOnly, constant=True)
    is3D = Property(bool, _is3D, constant=True)
    is2D = Property(bool, _is2D, constant=True)

    # Description of the attribute
    descriptionChanged = Signal()
    description = Property(str, _get_description, _set_description, notify=descriptionChanged)

    # Definition of the attribute
    desc = Property(desc.Attribute, lambda self: self.attributeDesc, constant=True)

    valueChanged = Signal()
    value = Property(Variant, _get_value, _set_value, notify=valueChanged)
    valueStr = Property(Variant, getValueStr, notify=valueChanged)
    evalValue = Property(Variant, getEvalValue, notify=valueChanged)
    isOutput = Property(bool, isOutput.fget, constant=True)
    isLinkChanged = Signal()
    isLink = Property(bool, isLink.fget, notify=isLinkChanged)
    isLinkNested = isLink
    hasOutputConnectionsChanged = Signal()
    hasOutputConnections = Property(bool, hasOutputConnections.fget, notify=hasOutputConnectionsChanged)

    linkedInAttributesChanged = Signal()
    linkedInAttributes = Property(Variant, getLinkedInAttributes, notify=linkedInAttributesChanged)
    linkedOutAttributesChanged = Signal()
    linkedOutAttributes = Property(Variant, getLinkedOutAttributes, notify=linkedOutAttributesChanged)

    isDefault = Property(bool, _isDefault, notify=valueChanged)
    linkParam = Property(BaseObject, getLinkParam, notify=isLinkChanged)
    rootLinkParam = Property(BaseObject, lambda self: self.getLinkParam(recursive=True),
                             notify=isLinkChanged)
    node = Property(BaseObject, node.fget, constant=True)
    enabledChanged = Signal()
    enabled = Property(bool, getEnabled, setEnabled, notify=enabledChanged)
    invalidate = Property(bool, lambda self: self._invalidate, constant=True)
    uidIgnoreValue = Property(Variant, getUidIgnoreValue, constant=True)
    validValueChanged = Signal()
    validValue = Property(bool, getValidValue, setValidValue, notify=validValueChanged)
    root = Property(BaseObject, root.fget, constant=True)


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
        if (linkParam := self.getLinkParam()) is not None:
            return linkParam.getValues()
        return self._values if self._values is not None else self.desc._values

    def conformValue(self, val):
        """ Conform 'val' to the correct type and check for its validity """
        return self.desc.conformValue(val)

    def validateValue(self, value):
        if self.desc.exclusive:
            return self.conformValue(value)

        if isinstance(value, str):
            value = value.split(',')

        if not isinstance(value, Iterable):
            raise ValueError("Non exclusive ChoiceParam value should be iterable (param:{}, value:{}, type:{})".
                             format(self.name, value, type(value)))
        return [self.conformValue(v) for v in value]

    def _set_value(self, value):
        # Handle alternative serialization for ChoiceParam with overriden values.
        serializedValueWithValuesOverrides = isinstance(value, dict)
        if serializedValueWithValuesOverrides:
            super()._set_value(value[self.desc._OVERRIDE_SERIALIZATION_KEY_VALUE])
            self.setValues(value[self.desc._OVERRIDE_SERIALIZATION_KEY_VALUES])
        else:
            super()._set_value(value)

    def setValues(self, values):
        if values == self._values:
            return
        self._values = values
        self.valuesChanged.emit()

    def getExportValue(self):
        useStandardSerialization = self.isLink or not self.desc._saveValuesOverride or \
            self._values is None

        if useStandardSerialization:
            return super().getExportValue()

        return {
            self.desc._OVERRIDE_SERIALIZATION_KEY_VALUE: self._value,
            self.desc._OVERRIDE_SERIALIZATION_KEY_VALUES: self._values,
        }

    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
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

    def getBaseType(self):
        return self.attributeDesc.elementDesc.__class__.__name__

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

    def _set_value(self, value):
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
            newValue = self.desc.validateValue(value)
            self.extend(newValue)
        self.requestGraphUpdate()

    def upgradeValue(self, exportedValues):
        if not isinstance(exportedValues, list):
            if isinstance(exportedValues, ListAttribute) or \
               Attribute.isLinkExpression(exportedValues):
                self._set_value(exportedValues)
                return
            raise RuntimeError("ListAttribute.upgradeValue: the given value is of type " +
                               str(type(exportedValues)) + " but a 'list' is expected.")

        attrs = []
        for v in exportedValues:
            a = attributeFactory(self.attributeDesc.elementDesc, None, self.isOutput,
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
        attrs = [attributeFactory(self.attributeDesc.elementDesc, v, self.isOutput, self.node, self)
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
            return self.getLinkParam().asLinkExpr()
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
        if self.attributeDesc.joinChar == ' ':
            return self.attributeDesc.joinChar.join([v.getValueStr(withQuotes=withQuotes)
                                                     for v in self.value])
        v = self.attributeDesc.joinChar.join([v.getValueStr(withQuotes=False)
                                              for v in self.value])
        if withQuotes and v:
            return f'"{v}"'
        return v

    def updateInternals(self):
        super().updateInternals()
        for attr in self._value:
            attr.updateInternals()

    @property
    def isLinkNested(self) -> bool:
        """ Whether the attribute or any of its elements is a link to another attribute. """
        # note: directly use self.node.graph._edges to avoid using the property that may become
        # invalid at some point
        return self.isLink \
            or self.node.graph and self.isInput and self.node.graph._edges \
            and any(v in self.node.graph._edges.keys() for v in self._value)

    # override
    @property
    def hasOutputConnections(self):
        """ Whether the attribute has output connections, i.e is the source of at least one edge. """

        # safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False

        return next((edge for edge in self.node.graph.edges.values() if edge.src == self), None) is not None or \
            any(attr.hasOutputConnections for attr in self._value if hasattr(attr, 'hasOutputConnections'))

    # override
    def getInputConnections(self) -> list["Edge"]:
        if not self.node.graph or not self.node.graph.edges:
            return []

        return [edge for edge in self.node.graph.edges.values() if edge.dst == self or edge.dst in self._value]

    # override
    def getOutputConnections(self) -> list["Edge"]:
        if not self.node.graph or not self.node.graph.edges:
            return []

        return [edge for edge in self.node.graph.edges.values() if edge.src == self or edge.src in self._value]

    # Override value property setter
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)
    baseType = Property(str, getBaseType, constant=True)
    isLinkNested = Property(bool, isLinkNested.fget)
    hasOutputConnections = Property(bool, hasOutputConnections.fget, notify=Attribute.hasOutputConnectionsChanged)


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

    def _set_value(self, exportedValue):
        value = self.validateValue(exportedValue)
        if isinstance(value, dict):
            # set individual child attribute values
            for key, v in value.items():
                self._value.get(key).value = v
        elif isinstance(value, (list, tuple)):
            if len(self.desc._groupDesc) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self.desc._groupDesc, value):
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
            if len(self.desc._groupDesc) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self.desc._groupDesc, value):
                self._value.get(attrDesc.name).upgradeValue(v)
        else:
            raise AttributeError(f"Failed to set on GroupAttribute: {str(value)}")

    def initValue(self):
        self._value = DictModel(keyAttrName='name', parent=self)
        subAttributes = []
        for subAttrDesc in self.attributeDesc.groupDesc:
            childAttr = attributeFactory(subAttrDesc, None, self.isOutput, self.node, self)
            subAttributes.append(childAttr)
            childAttr.valueChanged.connect(self.valueChanged)
        self._value.reset(subAttributes)

    def resetToDefaultValue(self):
        for attrDesc in self.desc._groupDesc:
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
        if self.attributeDesc.brackets is not None:
            if len(self.attributeDesc.brackets) == 2:
                strBegin = self.attributeDesc.brackets[0]
                strEnd = self.attributeDesc.brackets[1]
            else:
                raise AttributeError(f"Incorrect brackets on GroupAttribute: {self.attributeDesc.brackets}")

        # particular case when using space separator
        spaceSep = self.attributeDesc.joinChar == ' '

        # sort values based on child attributes group description order
        sortedSubValues = [self._value.get(attr.name).getValueStr(withQuotes=spaceSep)
                           for attr in self.attributeDesc.groupDesc]
        s = self.attributeDesc.joinChar.join(sortedSubValues)

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
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)


class MapAttribute(Attribute):
    """ 
    Map attribute composed of (string, Attribute) pairs.
    """

    class Pair(BaseObject):
        """ 
        Pair of (string, Attribute) for MapAttribute model.
        """
        def __init__(self, key: str, attribute: Attribute, parent=None):
            super().__init__(parent)
            self._key = key
            self._attribute = attribute

        def getKey(self) -> str:
            return self._key
        
        def getAttribute(self) -> Attribute:
            return self._attribute

        key = Property(str, getKey, constant=True)
        attribute = Property("QVariant", getAttribute, constant=True)

    def __init__(self, node, attributeDesc: desc.MapAttribute, isOutput: bool,
                 root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)

    def _set_value(self, value):
        # Link to another attribute
        if isinstance(value, MapAttribute) or Attribute.isLinkExpression(value):
            self._value = value
        # New value
        else:
            newValue = self.desc.validateValue(value)
            for k, v in newValue.items():
                self.add(k, v)
            
    def upgradeValue(self, exportedValue):
        # TODO
        pass

    def initValue(self):
        self.resetToDefaultValue()

    def resetToDefaultValue(self):
        self._value = DictModel(keyAttrName='key', parent=self)
        self.valueChanged.emit()

    def uid(self):
        if isinstance(self.value, DictModel):
            uids = []
            for pair in self._value:
                if pair.attribute.invalidate:
                    uids.append(pair.key)
                    uids.append(pair.attribute.uid())
            return hashValue(uids)
        return super().uid()
            
    def _applyExpr(self):
        if not self.node.graph:
            return
        if isinstance(self._value, MapAttribute) or Attribute.isLinkExpression(self._value):
            super()._applyExpr()
        else:
            for pair in self._value:
                pair.attribute._applyExpr()

    def getExportValue(self):
        if self.isLink:
            return self.getLinkParam().asLinkExpr()
        return { pair.key: pair.attribute.getExportValue() for pair in self._value }

    def defaultValue(self):
        return {}

    def _isDefault(self) -> bool:
        return len(self._value) == 0
    
    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return { pair.key: pair.attribute.getPrimitiveValue(exportDefault=exportDefault) for pair in self._value }
        return { pair.key: pair.attribute.getPrimitiveValue(exportDefault=exportDefault) for pair in self._value
                if not pair.attribute.isDefault }

    def getValueStr(self, withQuotes=True):
        return "" # TOD0: json serialization?

    def updateInternals(self):
        super().updateInternals()
        for pair in self._value:
            pair.attribute.updateInternals()

    def key(self, attribute: Attribute) -> str:
        """ 
        Get the key of the given attribute. 
        :return: the corresponding key or None if not found
        """
        for pair in self._value:
            if attribute is pair.attribute:
                return pair.key
        return None
        
    def attribute(self, key: str) -> Attribute:
        """ 
        Get the attribute of the given key.
        :return: the corresponding attribute or None if not found
        """
        try:
            return self._value.get(key).attribute
        except KeyError:
            return None
        
    @raiseIfLink
    def add(self, key: str, value):
        """ Add a new pair (key, attribute) from given key and attribute. """
        attribute = attributeFactory(self.attributeDesc.itemDesc, value, self.isOutput, self.node, self)
        # Add new pair if key does not exist
        if self._value.get(key) is None:
            # Add new pair
            self._value.add(MapAttribute.Pair(key, attribute))
            self._applyExpr()
             # Update graph
            self.valueChanged.emit()
            self.requestGraphUpdate()

    @raiseIfLink
    def remove(self, key: str):
        """ Remove a pair (key, attribute) from a given key. """
        # Get pair from key
        pair = self._value.get(key)
        # Remove potential links
        if self.node.graph:
            from meshroom.core.graph import GraphModification
            with GraphModification(self.node.graph):
                if pair.attribute.isLink:
                    # delete edge if the attribute is linked
                    self.node.graph.removeEdge(pair.attribute)
        # Remove pair from model
        self._value.remove(pair)
        # Update graph
        self.valueChanged.emit()
        self.requestGraphUpdate()
    
    # Override value property
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)
