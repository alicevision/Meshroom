#!/usr/bin/env python
from __future__ import annotations

import copy
import os
import re
import threading
import weakref
import logging
import inspect

from collections.abc import Iterable, Sequence
from string import Template
from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, DictModel, Slot
from meshroom.core.desc.validators import NotEmptyValidator
from meshroom.core import desc, hashValue
from meshroom.core.keyValues import KeyValues
from meshroom.core.exception import InvalidEdgeError

from typing import TYPE_CHECKING, Optional

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
    # NOTE: This should be handled by the Node class, but we are currently limited by our core
    #       signal implementation that does not support emitting parameters.
    #       And using a lambda here to send the attribute as a parameter causes
    #       performance issues when using the pyside backend.
    attr.valueChanged.connect(attr._onValueChanged)
    return attr


class Attribute(BaseObject):
    """
    """
    LINK_EXPRESSION_REGEX = re.compile(r'^\{[A-Za-z]+[A-Za-z0-9_.\[\]]*\}$')
    VALID_IMAGE_SEMANTICS = ["image", "imageList", "sequence"]
    VALID_3D_EXTENSIONS = [".obj", ".stl", ".fbx", ".gltf", ".abc", ".ply"]
    VALID_TEXT_EXTENSIONS = [".txt", ".json", ".log", ".csv", ".md"]

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
        self._depth: int = root.depth + 1 if root is not None else 0
        self._exposed: bool = root.exposed if root is not None else attributeDesc.exposed
        self._invalidate = False if self._isOutput else attributeDesc.invalidate
        self._invalidationValue = ""  # invalidation value for output attributes
        self._value = None
        self._keyValues = None  # list of pairs (key, value) for keyable attribute
        self._linkExpression: Optional[str] = None
        self._initValue()

    def _getFullName(self) -> str:
        """
        Get the attribute name following the path from the node to the attribute.
        Return: nodeName.groupName.subGroupName.name
        """
        return f'{self.node.name}.{self._getRootName()}'

    def _getRootName(self) -> str:
        """
        Get the attribute name following the path from the root attribute.
        Return: groupName.subGroupName.name
        """
        if isinstance(self.root, ListAttribute):
            return f'{self.root.rootName}[{self.root.index(self)}]'
        elif isinstance(self.root, GroupAttribute):
            return f'{self.root.rootName}.{self._desc.name}'
        return self._desc.name

    def asLinkExpr(self) -> str:
        """
        Return the link expression for this Attribute.
        """
        return "{" + self._getFullName() + "}"

    def requestGraphUpdate(self):
        if self.node.graph:
            self.node.graph.markNodesDirty(self.node)
            self.node.graph.update()

    def requestNodeUpdate(self):
        # Update specific node information that do not affect the rest of the graph
        # (like internal attributes)
        if self.node:
            self.node.updateInternalAttributes()

    def executeValue(self, value):
        """
        Assume value is a callable
        Analyze value signature to detect if we want to use node or attr as parameter.
        This method may be removed when all the legacy code is transformed.

        Args:
            value (Callable): the callable to execute

        Return the result value of the callable
        """
        # The new behavior is to provide the node to the callable.
        # For compatibility with the old behavior providing the attribute, we check if the attribute is named "attr" and provide the attribute.
        params = inspect.signature(value).parameters
        if len(params) == 1 and list(params)[0] == "attr":
            return value(self)
        
        return value(self.node)

    def _initValue(self):
        """
        Initialize the attribute value.
        Called in the attribute factory for each attributes.
        """
        if self._desc.keyable:
            # Keyable attribute, initialize keyValues from attribute description
            self._keyValues = KeyValues(self._desc)
            # Send signal and updates if keyValues changed
            self._keyValues.pairsChanged.connect(self._onKeyValuesChanged)
        elif self._desc._valueType is not None:
            self._value = self._desc._valueType()

    def _getEvalValue(self):
        """
        Return the value of a the attribute.
        For string, expressions will be evaluated.
        """
        if isinstance(self.value, str):
            env = self.node.nodePlugin.configFullEnv if self.node.nodePlugin else os.environ
            substituted = Template(self.value).safe_substitute(env)
            try:
                varResolved = substituted.format(**self.node._expVars, **self.node._staticExpVars)
                return varResolved
            except (KeyError, IndexError):
                # Catch KeyErrors and IndexErros to be able to open files created prior to the
                # support of relative variables (when self.node._expVars was not used to evaluate
                # expressions in the attribute)
                return substituted
            except (ValueError):
                return ""
        return self.value

    def _getValue(self):
        """
        Return the value of the attribute or the linked attribute value.
        """
        if self.keyable:
            raise RuntimeError(f"Cannot get value of {self._getFullName()}, the attribute is keyable.")
        if self.isLink:
            return self._getInputLink().value
        self._resolveValue()
        return self._value

    def _resolveValue(self):
        """
        Hook for subclasses to resolve pending values before returning _value.
        Called by _getValue before returning self._value.
        Default implementation is a no-op.
        """
        pass

    def _setValue(self, value):
        """
        Set the attribute value from a given value, a given function or a given attribute.
        """
        if self._value == value:
            return
        if self._handleLinkValue(value):
            if self.keyable:
                self._keyValues.reset()
            return
        elif self.keyable and isinstance(value, dict):
            # keyable attribute initialize from a dict
            self.keyValues.resetFromDict(value)
        elif self.keyable:
            # keyable attribute but value is not a dict
            raise RuntimeError(f"Cannot set value of {self._getFullName()}, the attribute is keyable.")
        elif callable(value):
            # evaluate the function
            self._value = self.executeValue(value)
        else:
            # if we set a new value, we use the attribute descriptor validator to check the
            # validity of the value and apply some conversion if needed
            convertedValue = self.validateValue(value)
            self._value = convertedValue
            self.expressionApplied.emit()
        # Request graph update when input parameter value is set
        # and parent node belongs to a graph
        # Output attributes value are set internally during the update process,
        # which is why we do not trigger any update in this case
        # TODO: update only the nodes impacted by this change
        # TODO: only update the graph if this attribute participates to a UID
        if self.isInput:
            self.requestGraphUpdate()
            # TODO: only call update of the node if the attribute is internal
            # Internal attributes are set as inputs
            self.requestNodeUpdate()
        self.valueChanged.emit()

    def _getKeyValues(self):
        """
        Return the per-key values object of the attribute or of the linked attribute.
        """
        if not self.keyable:
            raise RuntimeError(f"Cannot get keyValues of {self._getFullName()}, the attribute is not keyable.")
        if self.isLink:
            return self._getInputLink().keyValues
        return self._keyValues

    def _handleLinkValue(self, value) -> bool:
        """
        Handle the assignment of a link if `value` is a serialized link expression
        or an in-memory Attribute reference.

        Returns:
            True if the value has been handled as a link, False otherwise.
        """
        isAttribute = isinstance(value, Attribute)
        isLinkExpression = Attribute.isLinkExpression(value)

        if not isAttribute and not isLinkExpression:
            return False

        if isAttribute:
            self._linkExpression = value.asLinkExpr()
            # If the value is a direct reference to an attribute, it can directly
            # be converted to an edge as the source attribute already exists in
            # memory.
            self._applyExpr()
        elif isLinkExpression:
            self._linkExpression = value
        return True

    def _applyExpr(self):
        """
        For string parameters with an expression (when loaded from file),
        this function convert the expression into a real edge in the graph
        and clear the string value.
        """
        if not self.isInput or not self._linkExpression:
            return

        if not (graph := self.node.graph):
            return

        link = self._linkExpression[1:-1]
        linkNodeName, linkAttrName = "", ""

        try:
            linkNodeName, linkAttrName = link.split(".", 1)
        except ValueError as err:
            logging.warning('Retrieve Connected Attribute from Expression failed.')
            logging.warning(f'Expression: "{link}"\nError: "{err}".')

        try:
            node = graph.node(linkNodeName)
            if node is None:
                raise InvalidEdgeError(self.fullName, link, "Source node does not exist.")
            attr = node.attribute(linkAttrName)
            if attr is None:
                raise InvalidEdgeError(self.fullName, link, "Source attribute does not exist.")
            attr.connectTo(self)
        except InvalidEdgeError as err:
            logging.warning(err)
        except Exception as err:
            logging.warning("An unexpected error happened during edge creation.")
            logging.warning(f"Expression '{self._linkExpression}': {err}.")

        self._linkExpression = None
        self.resetToDefaultValue()

    def resetToDefaultValue(self):
        """
        Reset the attribute to its default value.
        """
        if self.keyable:
            self._value = None
            self._keyValues.reset()
        else:
            self._setValue(copy.copy(self.getDefaultValue()))

    def getDefaultValue(self):
        """
        Get the attribute default value.
        """
        if callable(self._desc.value):
            try:
                return self.executeValue(self._desc.value)
            except Exception as exc:
                if not self.node.isCompatibilityNode:
                    logging.warning(f"Failed to evaluate 'defaultValue' (node lambda) for attribute '{self.fullName}': {exc}")
                return None
        # keyable attribute default value
        if self.keyable:
            return {}
        # If the node's desc value is None and this is an input attribute with a known value type,
        # return the type's default value instead of None
        if self._desc.value is None and not self._isOutput and self._desc._valueType is not None:
            return self._desc._valueType()
        # Need to force a copy, for the case where the value is a list
        # (avoid reference to the desc value)
        return copy.copy(self._desc.value)

    def getSerializedValue(self):
        """
        Get the attribute value serialized.
        """
        if self.isLink:
            return self._getInputLink().asLinkExpr()
        if self.keyable:
            return self._keyValues.getSerializedValues()
        if self.isOutput and self._desc.isExpression:
            return self.getDefaultValue()
        return self.value

    def getPrimitiveValue(self, exportDefault=True):
        return self._value

    def getValueStr(self, withQuotes=True) -> str:
        """
        Return the value formatted as a string with quotes to deal with spaces.
        If it is a string, expressions will be evaluated.
        If it is an empty string, it will returns 2 quotes.
        If it is an empty list, it will returns a really empty string.
        If it is a list with one empty string element, it will returns 2 quotes.
        """
        # Keyable attribute, for now return the list of pairs as a JSON sting
        if self.keyable:
            return self._keyValues.getJson()
        # ChoiceParam with multiple values should be combined
        if isinstance(self._desc, desc.ChoiceParam) and not self._desc.exclusive:
            # Ensure value is a list as expected
            try:
                assert (isinstance(self.value, Sequence) and not isinstance(self.value, str))
            except AssertionError as e:
                logging.error(f"Attribute {self._getFullName()} value contains an error ({self.value}, {type(self.value)})")
                raise e
            v = self._desc.joinChar.join(self._getEvalValue())
            if withQuotes and v:
                return f'"{v}"'
            return v
        # String, File, single value Choice are based on strings and should includes quotes
        # to deal with spaces
        if withQuotes and isinstance(self._desc, (desc.StringParam, desc.File, desc.ChoiceParam)):
            return f'"{self._getEvalValue()}"'
        return str(self._getEvalValue())

    def validateValue(self, value):
        """
        Ensure value is compatible with the attribute description and convert value if needed.
        """
        return self._desc.validateValue(value)

    def upgradeValue(self, exportedValue):
        """
        Upgrade the attribute value within a compatibility node.
        """
        self._setValue(exportedValue)

    def _isDefault(self):
        if self.keyable:
            return len(self._keyValues.pairs) == 0
        else:
            return self._getValue() == self.getDefaultValue()

    def _is2dDisplayable(self) -> bool:
        """
        Return True if the current attribute is considered as a displayable 2D file.
        """
        if not self._desc.semantic:
            return False
        return next((imageSemantic for imageSemantic in Attribute.VALID_IMAGE_SEMANTICS
                     if self._desc.semantic == imageSemantic), None) is not None

    def _is3dDisplayable(self) -> bool:
        """
        Return True if the current attribute is considered as a displayable 3D file.
        """
        if self._desc.semantic == "3d":
            return True

        # If the attribute is a File attribute, it is an instance of str and can be iterated over
        hasSupportedExt = isinstance(self.value, str) and any(ext in self.value for ext in Attribute.VALID_3D_EXTENSIONS)
        if hasSupportedExt:
            return True

        return False

    def _isTextDisplayable(self) -> bool:
        """
        Return True if the current attribute is considered as a displayable text file.
        """
        if self._desc.semantic == "textFile":
            return True

        # If the attribute is a File attribute, it is an instance of str and can be iterated over
        hasSupportedExt = isinstance(self.value, str) and any(self.value.endswith(ext) for ext in Attribute.VALID_TEXT_EXTENSIONS)
        if hasSupportedExt:
            return True

        return False

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
            linkRootAttribute = self._getInputLink(recursive=True)
            return linkRootAttribute.uid()
        if self.keyable:
            return self._keyValues.uid()
        if isinstance(self._value, (list, tuple, set,)):
            # non-exclusive choice param
            # hash of sorted values hashed
            return hashValue([hashValue(v) for v in sorted(self._value)])
        return hashValue(self._value)

    def updateInternals(self):
        """
        Update attribute internal properties.
        """
        # Emit if the enable status has changed
        self._setEnabled(self._getEnabled())

    def getErrorMessages(self) -> list[str]:
        """ Execute the validators and aggregate the error messages if there are any. """
        result = []

        for validator in self.desc.validators:
            isValid, errorMessages = validator(self.node, self)

            if isValid:
                continue

            for errorMessage in errorMessages:
                result.append(errorMessage)

        return result

    def _isValid(self) -> bool:
        """ Check the validation and return False if any validator returns (False, errors). """
        for validator in self.desc.validators:
            isValid, _ = validator(self.node, self)

            if not isValid:
                return False

        return True

    def _isMandatory(self) -> bool:
        """ An attribute is considered as mandatory if it contains a NotEmptyValidator. """
        for validator in self.desc.validators:
            if isinstance(validator, NotEmptyValidator):
                return True

        return False

    def _getEnabled(self) -> bool:
        if callable(self._desc.enabled):
            try:
                return self._desc.enabled(self.node)
            except Exception as exc:
                if not self.node.isCompatibilityNode:
                    logging.warning(f"Failed to evaluate 'enabled' (node lambda) for attribute '{self.fullName}': {exc}")
                return True
        return self._desc.enabled

    def _setEnabled(self, v):
        if self._enabled == v:
            return
        self._enabled = v
        self.enabledChanged.emit()

    def _isLink(self) -> bool:
        """
        Whether the attribute is a link to another attribute.
        """
        return bool(self.node.graph and self.isInput and self.node.graph._edges and self in self.node.graph._edges.keys())

    def _getInputLink(self, recursive=False) -> Attribute:
        """
        Return the direct upstream connected attribute.
        :param recursive: recursive call, return the root attribute
        """
        if not self.isLink:
            return None
        linkAttribute = self.node.graph.edge(self).src
        if recursive and linkAttribute.isLink:
            return linkAttribute._getInputLink(recursive)
        return linkAttribute

    def _getOutputLinks(self) -> list[Attribute]:
        """
        Return the list of direct downstream connected attributes.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return []
        return [edge.dst for edge in self.node.graph.edges.values() if edge.src == self]

    def _getAllInputLinks(self) -> list[Attribute]:
        """
        Return the list of upstream connected attributes for the attribute or any of its elements.
        """
        inputLink = self._getInputLink()
        if inputLink is None:
            return []
        return [inputLink]

    def _getAllOutputLinks(self) -> list[Attribute]:
        """
        Return the list of downstream connected attributes for the attribute or any of its elements.
        """
        return self._getOutputLinks()

    def _hasAnyInputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is a link to another attribute.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False
        return next((edge for edge in self.node.graph.edges.values() if edge.dst == self), None) is not None

    def _hasAnyOutputLinks(self) -> bool:
        """
        Whether the attribute or any of its elements is linked by another attribute.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return False
        return next((edge for edge in self.node.graph.edges.values() if edge.src == self), None) is not None

    def _getFlatStaticChildren(self) -> list[Attribute]:
        """
        Return a list of all the attributes that refer to this Attribute as their parent through the
        "root" property. If no such attribute exist, return an empty list.
        The depth difference is not taken into account in the list, which is thus always flat.
        """
        return []

    def _validateIncomingConnection(self, connectingAttribute: Attribute) -> bool:
        """
        Validation of the connection of "connectingAttribute" on this Attribute.
        This method can be overridden.

        Args:
            connectingAttribute: the Attribute attempting to connect to this one.

        Returns:
            True if the connection is valid, False otherwise.
        """
        return self.baseType == connectingAttribute.baseType

    def connectTo(self, dstAttribute: Attribute) -> tuple[list[list[Attribute]], list[list[Attribute]]]:
        """
        Connect this Attribute to "dstAttribute".

        Args:
            dstAttribute: the destination Attribute

        Returns:
            A tuple containing:
                - a list containing pairs of the source and destination Attributes (as lists) for every created edge
                - a list containing pairs of the source and destination Attributes (as lists) for every deleted edge
        """
        if not (graph := self.node.graph):
            return [], []

        deletedEdges = []
        if isinstance(dstAttribute.root, Attribute):
            deletedEdges = dstAttribute.root.disconnectEdge()

        connectedEdge, deletedEdge = graph.addEdge(self, dstAttribute)
        if deletedEdge:
            deletedEdges.append(deletedEdge)

        return [connectedEdge], deletedEdges

    def disconnectEdge(self):
        """
        Disconnect and remove the edge connected to this Attribute.

        Returns:
            A list of all the Edge objects that were deleted during the disconnection.
        """
        if not (graph := self.node.graph):
            return []

        deletedEdges = []
        edge = graph.removeEdge(self)
        if edge:
            deletedEdges.append(edge)

        if isinstance(self.root, Attribute):
            deletedEdges += self.root.disconnectEdge()

        return deletedEdges

    # Slots

    @Slot()
    def _onKeyValuesChanged(self):
        """
        For keyable attribute, when the list or pairs (key, value) is modified this method should be called.
        Emit Attribute.valueChanged and update node / graph like _setValue().
        """
        if self.isInput:
            self.requestGraphUpdate()
            self.requestNodeUpdate()
        self.valueChanged.emit()

    @Slot()
    def _onValueChanged(self):
        self.node._onAttributeChanged(self)

    @Slot(str, result=bool)
    def matchText(self, text: str) -> bool:
        return self.label.lower().find(text.lower()) > -1

    @Slot(BaseObject, result=bool)
    def validateIncomingConnection(self, connectingAttribute: Attribute) -> bool:
        """
        Return True if this Attribute can receive a connection from
        "connectingAttribute", False otherwise.
        """
        return self._validateIncomingConnection(connectingAttribute)

    # Properties and signals

    # The node that contains this attribute.
    node = Property(BaseObject, lambda self: self._node(), constant=True)
    # The attribute that contains this attribute.
    root = Property(BaseObject, lambda self: self._root() if self._root else None, constant=True)
    # The attribute name following the path from the node to the attribute.
    fullName = Property(str, _getFullName, constant=True)
    # The attribute name following the path from the root attribute.
    rootName = Property(str, _getRootName, constant=True)
    # The description object of the attribute.
    desc = Property(desc.Attribute, lambda self: self._desc, constant=True)
    # The name of the attribute.
    name = Property(str, lambda self: self._desc._name, constant=True)
    # The human-readable label for the attribute.
    label = Property(str, lambda self: self._desc.label, constant=True)
    # The type of attribute as a string.
    type = Property(str, lambda self: self._desc.type, constant=True)
    # The type of the elements of the attribute as a string.
    baseType = Property(str, lambda self: self._desc.type, constant=True)
    # Whether the attribute is a node input attribute.
    isInput = Property(bool, lambda self: not self._isOutput, constant=True)
    # Whether the attribute is a node output attribute.
    isOutput = Property(bool, lambda self: self._isOutput, constant=True)
    # Whether the attribute is a read-only attribute.
    isReadOnly = Property(bool, lambda self: not self._isOutput and self.node.isCompatibilityNode, constant=True)
    # Whether changing this attribute invalidates cached results.
    invalidate = Property(bool, lambda self: self._invalidate, constant=True)
    # Whether this attribute is enabled.
    enabledChanged = Signal()
    enabled = Property(bool, _getEnabled, _setEnabled, notify=enabledChanged)
    # Depth level of this attribute.
    depth = Property(int, lambda self: self._depth, constant=True)
    # Whether the attribute is exposed (if it has a parent, the parent's value
    # takes precedence over the description's).
    exposed = Property(bool, lambda self: self._exposed, constant=True)

    # Attribute value properties and signals
    valueChanged = Signal()
    value = Property(Variant, _getValue, _setValue, notify=valueChanged)
    evalValue = Property(Variant, _getEvalValue, notify=valueChanged)
    # Whether the attribute can have a distinct value per key.
    keyable = Property(bool, lambda self: self._desc.keyable, constant=True)
    # The list of pairs (key, value) of the attribute.
    keyValues = Property(Variant, _getKeyValues, notify=valueChanged)

    # Whether the attribute value is the default value.
    isDefault = Property(bool, _isDefault, notify=valueChanged)
    # Whether the attribute value is valid.
    isValid = Property(bool, _isValid, notify=valueChanged)
    # Whether the attribute value is displayable in 2d.
    is2dDisplayable = Property(bool, _is2dDisplayable, constant=True)
    # Whether the attribute value is displayable in 3d.
    is3dDisplayable = Property(bool, _is3dDisplayable, constant=True)
    # Whether the attribute value is displayable as text.
    isTextDisplayable = Property(bool, _isTextDisplayable, constant=True)
    # Whether the attribute is a shape or a shape list, managed by the ShapeEditor and ShapeViewer.
    hasDisplayableShape = Property(bool, lambda self: False, constant=True)

    # Attribute link properties and signals
    inputLinksChanged = Signal()
    outputLinksChanged = Signal()

    # Whether the attribute is a link to another attribute.
    isLink = Property(bool, _isLink, notify=inputLinksChanged)
    # The upstream connected root attribute.
    inputRootLink = Property(Variant, lambda self: self._getInputLink(recursive=True), notify=inputLinksChanged)
    # The upstream connected attribute.
    inputLink = Property(BaseObject, _getInputLink, notify=inputLinksChanged)
    # The list of downstream connected attributes.
    outputLinks = Property(Variant, _getOutputLinks, notify=outputLinksChanged)
    # The list of upstream connected attributes for the attribute or any of its elements.
    allInputLinks = Property(Variant, _getAllInputLinks, notify=inputLinksChanged)
    # The list of downstream connected attributes for the attribute or any of its elements.
    allOutputLinks = Property(Variant, _getAllOutputLinks, notify=outputLinksChanged)
    # Whether the attribute or any of its elements is a link to another attribute.
    hasAnyInputLinks = Property(bool, _hasAnyInputLinks, notify=inputLinksChanged)
    # Whether the attribute or any of its elements is linked by another attribute.
    hasAnyOutputLinks = Property(bool, _hasAnyOutputLinks, notify=outputLinksChanged)
    # The list of attributes that refer to this one as their parent.
    flatStaticChildren = Property(Variant, _getFlatStaticChildren, constant=True)

    expressionApplied = Signal()

    errorMessageChanged = Signal()
    errorMessages = Property(Variant, lambda self: self.getErrorMessages(), notify=errorMessageChanged)
    isMandatory = Property(bool, _isMandatory, constant=True )    

def raiseIfLink(func):
    """
    If Attribute instance is a link, raise a RuntimeError.
    """
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
        if (linkParam := self._getInputLink()) is not None:
            return linkParam.getValues()
        return self._values if self._values is not None else self._desc._values

    def setValues(self, values):
        if values == self._values:
            return
        self._values = values
        self.valuesChanged.emit()

    # Override
    def validateValue(self, value):
        if self._desc.exclusive:
            return self._conformValue(value)
        if isinstance(value, str):
            value = value.split(',')
        if not isinstance(value, Iterable):
            raise ValueError(f"Non exclusive ChoiceParam value should be iterable (param: {self.name}, "
                             f"value: {value}, type: {type(value)})")
        return [self._conformValue(v) for v in value]

    def _conformValue(self, val):
        """
        Conform 'val' to the correct type and check for its validity
        """
        return self._desc.conformValue(val)

    # Override
    def _setValue(self, value):
        # Handle alternative serialization for ChoiceParam with overriden values.
        serializedValueWithValuesOverrides = isinstance(value, dict)
        if serializedValueWithValuesOverrides:
            super()._setValue(value[self._desc._OVERRIDE_SERIALIZATION_KEY_VALUE])
            self.setValues(value[self._desc._OVERRIDE_SERIALIZATION_KEY_VALUES])
        else:
            super()._setValue(value)

    # Override
    def getSerializedValue(self):
        useStandardSerialization = self.isLink or not self._desc._saveValuesOverride or \
            self._values is None
        if useStandardSerialization:
            return super().getSerializedValue()
        return {
            self._desc._OVERRIDE_SERIALIZATION_KEY_VALUE: self._value,
            self._desc._OVERRIDE_SERIALIZATION_KEY_VALUES: self._values,
        }

    value = Property(Variant, Attribute._getValue, _setValue, notify=Attribute.valueChanged)
    valuesChanged = Signal()
    values = Property(Variant, getValues, setValues, notify=valuesChanged)


class ListAttribute(Attribute):

    # Sentinel to distinguish 'no pending dynamic value' from 'pending reset to empty'
    _NO_PENDING_VALUE = object()

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
        """
        Returns child attribute at index 'idx'.
        """
        # Implement 'at' rather than '__getitem__'
        # since the later is called spuriously when object is used in QML
        return self.value.at(idx)

    def index(self, item):
        return self.value.indexOf(item)

    @raiseIfLink
    def append(self, value):
        self.extend([value])

    @raiseIfLink
    def extend(self, values):
        self.insert(len(self), values)

    @raiseIfLink
    def insert(self, index, value):
        if self._value is None:
            self._value = ListModel(parent=self)
        values = value if isinstance(value, list) else [value]
        attrs = [attributeFactory(self._desc.elementDesc, v, self.isOutput, self.node, self)
                 for v in values]
        self._value.insert(index, attrs)
        self._applyExpr()
        self.valueChanged.emit()
        if self.isInput:
            self.requestGraphUpdate()

    @raiseIfLink
    def remove(self, index, count=1):
        if self._value is None:
            return
        if self.node.graph and self.isInput:
            from meshroom.core.graph import GraphModification
            with GraphModification(self.node.graph):
                # remove potential links
                for i in range(index, index + count):
                    attr = self._value.at(i)
                    if attr.isLink:
                        # delete edge if the attribute is linked
                        self.node.graph.removeEdge(attr)
        self._value.removeAt(index, count)
        if self.isInput:
            self.requestGraphUpdate()
        self.valueChanged.emit()

    # Override
    def _initValue(self):
        self._dynamicValueLock = threading.Lock()
        self._dynamicValue = ListAttribute._NO_PENDING_VALUE
        self.resetToDefaultValue()

    # Override
    def _setValue(self, value):
        if self.isOutput:
            # For output attributes (set during processChunk in a worker thread,
            # or during loadOutputAttr in the TaskThread), store raw values without
            # creating QObject children to avoid cross-thread parenting issues.
            # The raw values are:
            # - serialized by saveOutputAttr via getPrimitiveValue
            # - materialized into QObjects lazily by _getValue on the main thread
            with self._dynamicValueLock:
                if value is None:
                    self._dynamicValue = None  # pending reset
                else:
                    self._dynamicValue = self._desc.validateValue(value)
            return

        # Input attribute path: handle None
        if value is None:
            if self.node.graph and self._value is not None and len(self._value) > 0:
                self.remove(0, len(self))
            if self._value is None:
                self._value = ListModel(parent=self)
            self.valueChanged.emit()
            return

        if self.node.graph:
            self.remove(0, len(self))
        if self._handleLinkValue(value):
            return
        # New value
        else:
            # During initialization self._value may not be set
            if self._value is None:
                self._value = ListModel(parent=self)
            newValue = self._desc.validateValue(value)
            self.extend(newValue)
        if self.isInput:
            self.requestGraphUpdate()

    # Override
    def _applyExpr(self):
        if self._linkExpression:
            super()._applyExpr()
        else:
            for value in self._value:
                value._applyExpr()

    def _populateFromDynamicValue(self, value):
        """Store raw dynamic values for lazy materialization.

        Does NOT create QObject children — safe to call from any thread.
        The actual ListModel population happens lazily in _getValue()
        when the main thread (e.g. QML) reads the value.
        """
        with self._dynamicValueLock:
            if value is None:
                self._dynamicValue = None  # pending reset
            else:
                self._dynamicValue = self._desc.validateValue(value)
        self.valueChanged.emit()

    # Override
    def resetToDefaultValue(self):
        self._value = ListModel(parent=self)
        self.valueChanged.emit()

    # Override
    def getDefaultValue(self) -> list:
        return []

    # Override
    def getSerializedValue(self):
        if self.isLink:
            return self._getInputLink().asLinkExpr()
        return [attr.getSerializedValue() for attr in self._value]

    value = Property(Variant, Attribute._getValue, _setValue, notify=Attribute.valueChanged)

    # Override
    def _resolveValue(self):
        """
        Lazily materialize QObject children from pending raw dynamic values.
        Called by Attribute._getValue (base) before returning self._value.
        This hook dispatches via normal Python MRO, bypassing PySide Property
        getter dispatch limitations.
        Must only create QObjects on the main thread to avoid cross-thread issues.
        """
        if self._dynamicValue is not ListAttribute._NO_PENDING_VALUE:
            if threading.current_thread() is threading.main_thread():
                self._materializeDynamicValue()

    def _materializeDynamicValue(self):
        """
        Create QObject children in the ListModel from pending raw dynamic values.
        Must only be called on the main thread.
        """

        # Thread proof reading of dynamic value
        with self._dynamicValueLock:
            pendingValue = self._dynamicValue
            self._dynamicValue = ListAttribute._NO_PENDING_VALUE

        # Create an empty list if the value is None
        if self._value is None:
            self._value = ListModel(parent=self)
        elif len(self._value) > 0:
            # Erase all items before reassigning
            self._value.removeAt(0, len(self._value))
        
        # Effectively create the objects from the raw data
        if pendingValue:
            attrs = [attributeFactory(self._desc.elementDesc, v, self.isOutput, self.node, self)
                     for v in pendingValue]
            self._value.insert(0, attrs)
        
        self.valueChanged.emit()

    # Override
    def getPrimitiveValue(self, exportDefault=True):
        # If there is a pending dynamic value (set or reset), return it directly
        # without touching the ListModel (which may be on a different thread).
        with self._dynamicValueLock:
            if self._dynamicValue is not ListAttribute._NO_PENDING_VALUE:
                if self._dynamicValue is None:
                    return []
                return list(self._dynamicValue)
        
        if exportDefault:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value]
        return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value
                if not attr.isDefault]

    # Override
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

    # Override
    def upgradeValue(self, exportedValues):
        if self._handleLinkValue(exportedValues):
            return
        if not isinstance(exportedValues, list):
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

    # Override
    def uid(self):
        if isinstance(self.value, ListModel):
            uids = []
            for value in self.value:
                if value.invalidate:
                    uids.append(value.uid())
            return hashValue(uids)
        return super().uid()

    # Override
    def updateInternals(self):
        super().updateInternals()
        for attr in self._value:
            attr.updateInternals()

    # Override
    def _getAllInputLinks(self) -> list[Attribute]:
        """
        Return the list of upstream connected attributes for the attribute or any of its elements.
        """
        # Safety check to avoid evaluation errors
        if not self.node.graph or not self.node.graph.edges:
            return []
        return [edge.src for edge in self.node.graph.edges.values() if edge.dst == self or edge.dst in self._value]

    # Override
    def _getAllOutputLinks(self) -> list[Attribute]:
        """
        Return the list of downstream connected attributes for the attribute or any of its elements.
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
    isDefault = Property(bool, lambda self: len(self.value) == 0, notify=Attribute.valueChanged)
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

    # Override
    def _initValue(self):
        self._value = DictModel(keyAttrName='name', parent=self)
        subAttributes = []
        for subAttrDesc in self._desc.items:
            childAttr = attributeFactory(subAttrDesc, None, self.isOutput, self.node, self)
            subAttributes.append(childAttr)
            childAttr.valueChanged.connect(self.valueChanged)
        self._value.reset(subAttributes)

    # Override
    def _getValue(self):
        return self._value

    # Override
    def _setValue(self, exportedValue):
        if self._handleLinkValue(exportedValue):
            return

        value = self.validateValue(exportedValue)
        if isinstance(value, dict):
            # set individual child attribute values
            for key, v in value.items():
                self._value.get(key).value = v
        elif isinstance(value, (list, tuple)):
            if len(self._desc._items) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self._desc._items, value):
                self._value.get(attrDesc.name).value = v
        else:
            raise AttributeError(f"Failed to set on GroupAttribute: {str(value)}")

    # Override
    def _applyExpr(self):
        if self._linkExpression:
            super()._applyExpr()
        else:
            for value in self._value:
                value._applyExpr()

    # Override
    def resetToDefaultValue(self):
        for attrDesc in self._desc._items:
            self._value.get(attrDesc.name).resetToDefaultValue()

    # Override
    def getDefaultValue(self):
        return {key: attr.getDefaultValue() for key, attr in self._value.items()}

    # Override
    def getSerializedValue(self):
        if self.inputLink:
            return self.inputLink.asLinkExpr()
        return {key: attr.getSerializedValue() for key, attr in self._value.objects.items()}

    # Override
    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items()}
        return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items()
                if not attr.isDefault}

    # Override
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
                           for attr in self._desc.items]
        s = self._desc.joinChar.join(sortedSubValues)
        if withQuotes and not spaceSep:
            return f'"{strBegin}{s}{strEnd}"'
        return f'{strBegin}{s}{strEnd}'

    # Override
    def upgradeValue(self, exportedValue):
        if self._handleLinkValue(exportedValue):
            return

        value = self.validateValue(exportedValue)
        if isinstance(value, dict):
            # set individual child attribute values
            for key, v in value.items():
                if key in self._value.keys():
                    self._value.get(key).upgradeValue(v)
        elif isinstance(value, (list, tuple)):
            if len(self._desc._items) != len(value):
                raise AttributeError(f"Incorrect number of values on GroupAttribute: {str(value)}")
            for attrDesc, v in zip(self._desc._items, value):
                self._value.get(attrDesc.name).upgradeValue(v)
        else:
            raise AttributeError(f"Failed to set on GroupAttribute: {str(value)}")

    # Override
    def uid(self):
        if self.isLink:
            return super().uid()

        uids = []
        for _, v in self._value.items():
            if v.enabled and v.invalidate:
                uids.append(v.uid())
        return hashValue(uids)

    # Override
    def updateInternals(self):
        super().updateInternals()
        for attr in self._value:
            attr.updateInternals()

    # Override
    def _getFlatStaticChildren(self) -> list[Attribute]:
        attributes = []

        # Iterate over the values and add the flat children of every child (if they exist)
        for attribute in self.value:
            attributes.append(attribute)
            attributes += attribute.flatStaticChildren

        return attributes

    # Override
    def _validateIncomingConnection(self, connectingAttribute: Attribute) -> bool:
        valid = super()._validateIncomingConnection(connectingAttribute)

        if not valid:  # Attributes are not of the same base type
            return False

        return self._hasMatchingStructure(connectingAttribute)

    def _hasMatchingStructure(self, otherAttribute: Attribute) -> bool:
        """
        Check whether this GroupAttribute and another Attribute have matching structures.

        Attributes have matching structures if they have the same number of children and if, at each position,
        both Attributes have the same base type.

        Args:
            otherAttribute: the other Attribute to compare structure with

        Returns:
            True if both Attributes have the same structure, False otherwise
        """
        flatAttrs = self.flatStaticChildren
        otherFlatAttrs = otherAttribute.flatStaticChildren

        if len(flatAttrs) != len(otherFlatAttrs):
            return False

        for index, attribute in enumerate(flatAttrs):
            if attribute.baseType != otherFlatAttrs[index].baseType:
                return False

        return True

    # Override
    def connectTo(self, dstAttribute: GroupAttribute) -> tuple[list[list[Attribute]], list[list[Attribute]]]:
        """
        Connect this GroupAttribute to "dstAttribute". The nested attributes in the group
        are automatically connected.

        Args:
            dstAttribute: the destination Attribute

        Returns:
            A tuple containing:
                - a list containing pairs of the source and destination Attributes (as lists) for every created edge
                - a list containing pairs of the source and destination Attributes (as lists) for every deleted edge
        """
        nestedDstAttributes = list(dstAttribute.value)
        connectedEdges = []
        deletedEdges = []

        for index, nestedAttribute in enumerate(list(self.value)):
            # If the attributes are already connected, do not connect them again
            if not nestedDstAttributes[index] in nestedAttribute.outputLinks:
                connected, deleted = nestedAttribute.connectTo(nestedDstAttributes[index])
                connectedEdges += connected
                deletedEdges += deleted
        connected, deleted = super().connectTo(dstAttribute)
        connectedEdges += connected
        deletedEdges += deleted

        return connectedEdges, deletedEdges

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

    # Override
    @Slot(str, result=bool)
    def matchText(self, text: str) -> bool:
        return super().matchText(text) or any(c.matchText(text) for c in self._value)

    # Override value property
    value = Property(Variant, _getValue, _setValue, notify=Attribute.valueChanged)
    # Override flatStaticChildren property
    flatStaticChildren = Property(Variant, _getFlatStaticChildren, constant=True)
    isDefault = Property(bool, lambda self: all(v.isDefault for v in self.value),
                         notify=Attribute.valueChanged)


class GeometryAttribute(GroupAttribute):
    """
    GroupAttribute subtype tailored for geometry-specific handling.
    """

    def __init__(self, node, attributeDesc: desc.Geometry, isOutput: bool, root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)

    # Override
    # Signal observationsChanged should be emitted.
    def _setValue(self, exportedValue):
        super()._setValue(exportedValue)
        self.observationsChanged.emit()

    # Override
    # Signal observationsChanged should be emitted.
    def resetToDefaultValue(self):
        super().resetToDefaultValue()
        self.observationsChanged.emit()

    # Override
    # Signal observationsChanged should be emitted.
    def upgradeValue(self, exportedValue):
        super().upgradeValue(exportedValue)
        self.observationsChanged.emit()

    # Override
    # Fix missing link expression serialization.
    # Should be remove if link expression serialization is added in GroupAttribute.
    def getSerializedValue(self):
        if self.isLink:
            return self._getInputLink().asLinkExpr()
        return super().getSerializedValue()

    def getValueAsDict(self) -> dict:
        """
        Return the geometry attribute value as dict.
        For not keyable geometry, this is the same as getSerializedValue().
        For keyable geometry, the dict is indexed by key.
        """
        from collections import defaultdict
        outValue = defaultdict(dict)
        if not self.observationKeyable:
            return super().getSerializedValue()
        for attribute in self.value:
            if isinstance(attribute, GeometryAttribute):
                attributeDict = attribute.getValueAsDict()
                if attributeDict:
                    for key, value in attributeDict.items():
                        outValue[key][attribute.name] = value
            else:
                for pair in attribute.keyValues.pairs:
                    outValue[str(pair.key)][attribute.name] = pair.value
        return dict(outValue)

    def _hasKeyableChilds(self) -> bool:
        """
        Whether all child attributes are keyable.
        """
        return all((isinstance(attribute, GeometryAttribute) and attribute.observationKeyable) or
                    attribute.keyable for attribute in self.value)

    def _getNbObservations(self) -> int:
        """
        Return the geometry attribute number of observations.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        if self.observationKeyable:
            firstAttribute = next(iter(self.value.values()))
            if isinstance(firstAttribute, GeometryAttribute):
                return firstAttribute.nbObservations
            return len(firstAttribute.keyValues.pairs)
        return 1

    def _getObservationKeys(self) -> list:
        """
        Return the geometry attribute list of observation keys.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        if not self.observationKeyable:
            return []
        firstAttribute = next(iter(self.value.values()))
        if isinstance(firstAttribute, GeometryAttribute):
            return firstAttribute.observationKeys
        return firstAttribute.keyValues.getKeys()

    @Slot(str, result=bool)
    def hasObservation(self, key: str) -> bool:
        """
        Whether the geometry attribute has an observation for the given key.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        if not self.observationKeyable:
            return True
        return all((isinstance(attribute, GeometryAttribute) and attribute.hasObservation(key)) or
                   (not isinstance(attribute, GeometryAttribute) and attribute.keyValues.hasKey(key))
                   for attribute in self.value)

    @raiseIfLink
    def removeObservation(self, key: str):
        """
        Remove the geometry attribute observation for the given key.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        for attribute in self.value:
            if isinstance(attribute, GeometryAttribute):
                attribute.removeObservation(key)
            else:
                if attribute.keyable:
                    attribute.keyValues.remove(key)
                else:
                    attribute.resetToDefaultValue()
        self.observationsChanged.emit()

    @raiseIfLink
    def setObservation(self, key: str, observation: Variant):
        """
        Set the geometry attribute observation for the given key with the given observation.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        for attributeStr, value in observation.items():
            attribute = self.childAttribute(attributeStr)
            if attribute is None:
                raise RuntimeError(f"Cannot set geometry observation for attribute {self._getFullName()} \
                                   observation is incorrect.")
            if isinstance(attribute, GeometryAttribute):
                attribute.setObservation(key, value)
            else:
                if attribute.keyable:
                    attribute.keyValues.add(key, value)
                else:
                    attribute.value = value
        self.observationsChanged.emit()

    @Slot(str, result=Variant)
    def getObservation(self, key: str) -> Variant:
        """
        Return the geometry attribute observation for the given key.
        Note: Observation is a value defined across all child attributes for a specific key.
        """
        observation = {}
        for attribute in self.value:
            if isinstance(attribute, GeometryAttribute):
                geoObservation = attribute.getObservation(key)
                if geoObservation is None:
                    return None
                else:
                    observation[attribute.name] = geoObservation
            else:
                if attribute.keyable:
                    if attribute.keyValues.hasKey(key):
                        observation[attribute.name] = attribute.keyValues.getValueAtKeyOrDefault(key)
                    else:
                        return None
                else:
                    observation[attribute.name] = attribute.value
        return observation

    # Properties and signals
    # Emitted when a geometry observation changed.
    observationsChanged = Signal()
    # Whether the geometry attribute childs are keyable.
    observationKeyable = Property(bool, _hasKeyableChilds, constant=True)
    # The list of geometry observation keys.
    observationKeys = Property(Variant, _getObservationKeys, notify=observationsChanged)
    # The number of geometry observation defined.
    nbObservations = Property(int, _getNbObservations, notify=observationsChanged)


class ShapeAttribute(GroupAttribute):
    """
    GroupAttribute subtype tailored for shape-specific handling.
    """

    def __init__(self, node, attributeDesc: desc.Shape, isOutput: bool, root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)
        self._visible = True

    # Override
    # Connect geometry attribute valueChanged to emit geometryChanged signal.
    def _initValue(self):
        super()._initValue()
        # Using Attribute.valueChanged for the userName, userColor, geometry properties results
        # in a segmentation fault.
        # As a workaround, we manually connect valueChanged to shapeChanged or geometryChanged.
        self.value.get("userName").valueChanged.connect(self._onShapeChanged)
        self.value.get("userColor").valueChanged.connect(self._onShapeChanged)
        self.geometry.valueChanged.connect(self._onGeometryChanged)

    # Override
    # Fix missing link expression serialization.
    # Should be remove if link expression serialization is added in GroupAttribute.
    def getSerializedValue(self):
        if self.isLink:
            return self._getInputLink().asLinkExpr()
        return super().getSerializedValue()

    def getShapeAsDict(self) -> dict:
        """
        Return the shape attribute as dict with the shape file structure.
        """
        outDict = {
            "name": self.userName if self.userName else self.rootName,
            "type": self.type,
            "properties": {"color": self.userColor}
        }
        if not self.geometry.observationKeyable:
            # Not keyable geometry, use properties.
            outDict.get("properties").update(self.geometry.getSerializedValue())
        else:
            # Keyable geometry, use observations.
            outDict.update({"observations": self.geometry.getValueAsDict()})
        return outDict

    def _getVisible(self) -> bool:
        """
        Return whether the shape attribute is visible for display.
        """
        return self._visible

    def _setVisible(self, visible: bool):
        """
        Set the shape attribute visibility for display.
        """
        self._visible = visible
        self.shapeChanged.emit()

    def _getUserName(self) -> str:
        """
        Return the shape attribute user name for display.
        """
        return self.value.get("userName").value

    def _getUserColor(self) -> str:
        """
        Return the shape attribute user color for display.
        """
        return self.value.get("userColor").value

    @Slot()
    def _onShapeChanged(self):
        """
        Emit shapeChanged signal.
        Used when shape userName or userColor value changed.
        """
        self.shapeChanged.emit()

    @Slot()
    def _onGeometryChanged(self):
        """
        Emit geometryChanged signal.
        Used when geometry attribute value changed.
        """
        self.geometryChanged.emit()

    # Properties and signals
    # Emitted when a shape related property changed (color, visibility).
    shapeChanged = Signal()
    # Emitted when a shape observation changed.
    geometryChanged = Signal()
    # Whether the shape is displayable.
    isVisible = Property(bool, _getVisible, _setVisible, notify=shapeChanged)
    # The shape user name for display.
    userName = Property(str, _getUserName, notify=shapeChanged)
    # The shape user color for display.
    userColor = Property(str, _getUserColor, notify=shapeChanged)
    # The shape geometry group attribute.
    geometry = Property(Variant, lambda self: self.value.get("geometry"), notify=geometryChanged)
    # Override hasDisplayableShape property.
    hasDisplayableShape = Property(bool, lambda self: True, constant=True)


class ShapeListAttribute(ListAttribute):
    """
    ListAttribute subtype tailored for shape-specific handling.
    """

    def __init__(self, node, attributeDesc: desc.ShapeList, isOutput: bool, root=None, parent=None):
        super().__init__(node, attributeDesc, isOutput, root, parent)
        self._visible = True

    def getGeometriesAsDict(self):
        """
        Return the geometries values of the children of the shape list attribute.
        """
        return [shapeAttribute.geometry.getValueAsDict() for shapeAttribute in self.value]

    def getShapesAsDict(self):
        """
        Return the children of the shape list attribute.
        """
        return [shapeAttribute.getShapeAsDict() for shapeAttribute in self.value]

    def _getVisible(self) -> bool:
        """
        Return whether the shape list is visible for display.
        """
        if self.isLink:
            return self.inputLink.isVisible
        return self._visible

    def _setVisible(self, visible: bool):
        """
        Set the shape visibility for display.
        """
        if self.isLink:
            self.inputLink.isVisible = visible
        else:
            self._visible = visible
        for attribute in self.value:
            if isinstance(attribute, ShapeAttribute):
                attribute.isVisible = visible
        self.shapeListChanged.emit()

    # Properties and signals
    # Emitted when a shape list related property changed.
    shapeListChanged = Signal()
    # Whether the shape list is displayable.
    isVisible = Property(bool, _getVisible, _setVisible, notify=shapeListChanged)
    # Override hasDisplayableShape property.
    hasDisplayableShape = Property(bool, lambda self: True, constant=True)
