#!/usr/bin/env python
# coding:utf-8
import collections
import re
import weakref

from meshroom.common import BaseObject, Property, Variant, Signal, ListModel, DictModel, Slot
from meshroom.core import desc, pyCompatibility, hashValue


def attributeFactory(description, value, isOutput, node, root=None, parent=None):
    """
    Create an Attribute based on description type.

    Args:
        description: the Attribute description
        value:  value of the Attribute. Will be set if not None.
        isOutput: whether is Attribute is an output attribute.
        node (Node): node owning the Attribute. Note that the created Attribute is not added to Node's attributes
        root: (optional) parent Attribute (must be ListAttribute or GroupAttribute)
        parent (BaseObject): (optional) the parent BaseObject if any
    """
    if isinstance(description, desc.GroupAttribute):
        cls = GroupAttribute
    elif isinstance(description, desc.ListAttribute):
        cls = ListAttribute
    else:
        cls = Attribute
    attr = cls(node, description, isOutput, root, parent)
    if value is not None:
        attr.value = value
    return attr


class Attribute(BaseObject):
    """
    """
    stringIsLinkRe = re.compile('^\{[A-Za-z]+[A-Za-z0-9_.]*\}$')

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        """
        Attribute constructor

        Args:
            node (Node): the Node hosting this Attribute
            attributeDesc (desc.Attribute): the description of this Attribute
            isOutput (bool): whether this Attribute is an output of the Node
            root (Attribute): (optional) the root Attribute (List or Group) containing this one
            parent (BaseObject): (optional) the parent BaseObject
        """
        super(Attribute, self).__init__(parent)
        self._name = attributeDesc.name
        self._root = None if root is None else weakref.ref(root)
        self._node = weakref.ref(node)
        self.attributeDesc = attributeDesc
        self._isOutput = isOutput
        self._value = attributeDesc.value
        self._label = attributeDesc.label

        # invalidation value for output attributes
        self._invalidationValue = ""

    @property
    def node(self):
        return self._node()

    @property
    def root(self):
        return self._root() if self._root else None

    def absoluteName(self):
        return '{}.{}.{}'.format(self.node.graph.name, self.node.name, self._name)

    def getFullName(self):
        """ Name inside the Graph: nodeName.name """
        if isinstance(self.root, ListAttribute):
            return '{}[{}]'.format(self.root.getFullName(), self.root.index(self))
        elif isinstance(self.root, GroupAttribute):
            return '{}.{}'.format(self.root.getFullName(), self._name)
        return '{}.{}'.format(self.node.name, self._name)

    def asLinkExpr(self):
        """ Return link expression for this Attribute """
        return "{" + self.getFullName() + "}"

    def getName(self):
        """ Attribute name """
        return self._name

    def getType(self):
        return self.attributeDesc.__class__.__name__

    def getLabel(self):
        return self._label

    def _get_value(self):
        return self.getLinkParam().value if self.isLink else self._value

    def _set_value(self, value):
        if self._value == value:
            return

        if isinstance(value, Attribute) or Attribute.isLinkExpression(value):
            # if we set a link to another attribute
            self._value = value
        else:
            # if we set a new value, we use the attribute descriptor validator to check the validity of the value
            # and apply some conversion if needed
            convertedValue = self.desc.validateValue(value)
            self._value = convertedValue
        # Request graph update when input parameter value is set
        # and parent node belongs to a graph
        # Output attributes value are set internally during the update process,
        # which is why we don't trigger any update in this case
        # TODO: update only the nodes impacted by this change
        # TODO: only update the graph if this attribute participates to a UID
        if self.isInput:
            self.requestGraphUpdate()
        self.valueChanged.emit()

    def resetValue(self):
        self._value = ""

    def requestGraphUpdate(self):
        if self.node.graph:
            self.node.graph.markNodesDirty(self.node)

    @property
    def isOutput(self):
        return self._isOutput

    @property
    def isInput(self):
        return not self._isOutput

    def uid(self, uidIndex=-1):
        """
        """
        # 'uidIndex' should be in 'self.desc.uid' but in the case of linked attribute
        # it will not be the case (so we cannot have an assert).
        if self.isOutput:
            # only dependent on the hash of its value without the cache folder
            return hashValue(self._invalidationValue)
        if self.isLink:
            return self.getLinkParam().uid(uidIndex)
        if isinstance(self._value, (list, tuple, set,)):
            # hash of sorted values hashed
            return hashValue([hashValue(v) for v in sorted(self._value)])
        return hashValue(self._value)

    @property
    def isLink(self):
        """ Whether the attribute is a link to another attribute. """
        # note: directly use self.node.graph._edges to avoid using the property that may become invalid at some point
        return self.node.graph and self.isInput and self in self.node.graph._edges.keys()

    @staticmethod
    def isLinkExpression(value):
        """
        Return whether the given argument is a link expression.
        A link expression is a string matching the {nodeName.attrName} pattern.
        """
        return isinstance(value, pyCompatibility.basestring) and Attribute.stringIsLinkRe.match(value)

    def getLinkParam(self):
        return self.node.graph.edge(self).src if self.isLink else None

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
            self.resetValue()
        elif self.isInput and Attribute.isLinkExpression(v):
            # value is a link to another attribute
            link = v[1:-1]
            linkNode, linkAttr = link.split('.')
            g.addEdge(g.node(linkNode).attribute(linkAttr), self)
            self.resetValue()

    def getExportValue(self):
        if self.isLink:
            return self.getLinkParam().asLinkExpr()
        if self.isOutput:
            return self.desc.value
        return self._value

    def getValueStr(self):
        if isinstance(self.attributeDesc, desc.ChoiceParam) and not self.attributeDesc.exclusive:
            assert(isinstance(self.value, collections.Sequence) and not isinstance(self.value, pyCompatibility.basestring))
            return self.attributeDesc.joinChar.join(self.value)
        if isinstance(self.attributeDesc, (desc.StringParam, desc.File)):
            return '"{}"'.format(self.value)
        return str(self.value)

    def defaultValue(self):
        return self.desc.value

    def _isDefault(self):
        return self._value == self.defaultValue()

    def getPrimitiveValue(self, exportDefault=True):
        return self._value

    name = Property(str, getName, constant=True)
    fullName = Property(str, getFullName, constant=True)
    label = Property(str, getLabel, constant=True)
    type = Property(str, getType, constant=True)
    desc = Property(desc.Attribute, lambda self: self.attributeDesc, constant=True)
    valueChanged = Signal()
    value = Property(Variant, _get_value, _set_value, notify=valueChanged)
    isOutput = Property(bool, isOutput.fget, constant=True)
    isLinkChanged = Signal()
    isLink = Property(bool, isLink.fget, notify=isLinkChanged)
    isDefault = Property(bool, _isDefault, notify=valueChanged)
    linkParam = Property(BaseObject, getLinkParam, notify=isLinkChanged)
    node = Property(BaseObject, node.fget, constant=True)


def raiseIfLink(func):
    """ If Attribute instance is a link, raise a RuntimeError."""
    def wrapper(attr, *args, **kwargs):
        if attr.isLink:
            raise RuntimeError("Can't modify connected Attribute")
        return func(attr, *args, **kwargs)
    return wrapper


class ListAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        super(ListAttribute, self).__init__(node, attributeDesc, isOutput, root, parent)
        self._value = ListModel(parent=self)

    def __len__(self):
        return len(self._value)

    def at(self, idx):
        """ Returns child attribute at index 'idx' """
        # implement 'at' rather than '__getitem__'
        # since the later is called spuriously when object is used in QML
        return self._value.at(idx)

    def index(self, item):
        return self._value.indexOf(item)

    def resetValue(self):
        self._value = ListModel(parent=self)

    def _set_value(self, value):
        if self.node.graph:
            self.remove(0, len(self))
        # Link to another attribute
        if isinstance(value, ListAttribute) or Attribute.isLinkExpression(value):
            self._value = value
        # New value
        else:
            self.desc.validateValue(value)
            self.extend(value)
        self.requestGraphUpdate()

    @raiseIfLink
    def append(self, value):
        self.extend([value])

    @raiseIfLink
    def insert(self, index, value):
        values = value if isinstance(value, list) else [value]
        attrs = [attributeFactory(self.attributeDesc.elementDesc, v, self.isOutput, self.node, self) for v in values]
        self._value.insert(index, attrs)
        self.valueChanged.emit()
        self._applyExpr()
        self.requestGraphUpdate()

    @raiseIfLink
    def extend(self, values):
        self.insert(len(self._value), values)

    @raiseIfLink
    def remove(self, index, count=1):
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

    def uid(self, uidIndex):
        if isinstance(self.value, ListModel):
            uids = []
            for value in self.value:
                if uidIndex in value.desc.uid:
                    uids.append(value.uid(uidIndex))
            return hashValue(uids)
        return super(ListAttribute, self).uid(uidIndex)

    def _applyExpr(self):
        if not self.node.graph:
            return
        if isinstance(self._value, ListAttribute) or Attribute.isLinkExpression(self._value):
            super(ListAttribute, self)._applyExpr()
        else:
            for value in self._value:
                value._applyExpr()

    def getExportValue(self):
        if self.isLink:
            return self.getLinkParam().asLinkExpr()
        return [attr.getExportValue() for attr in self._value]

    def defaultValue(self):
        return []

    def _isDefault(self):
        return len(self._value) == 0

    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value]
        else:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value if not attr.isDefault]

    def getValueStr(self):
        if isinstance(self.value, ListModel):
            return self.attributeDesc.joinChar.join([v.getValueStr() for v in self.value])
        return super(ListAttribute, self).getValueStr()

    # Override value property setter
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)


class GroupAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        super(GroupAttribute, self).__init__(node, attributeDesc, isOutput, root, parent)
        self._value = DictModel(keyAttrName='name', parent=self)

        subAttributes = []
        for subAttrDesc in self.attributeDesc.groupDesc:
            childAttr = attributeFactory(subAttrDesc, None, self.isOutput, self.node, self)
            subAttributes.append(childAttr)
            childAttr.valueChanged.connect(self.valueChanged)

        self._value.reset(subAttributes)

    def __getattr__(self, key):
        try:
            return super(GroupAttribute, self).__getattr__(key)
        except AttributeError:
            try:
                return self._value.get(key)
            except KeyError:
                raise AttributeError(key)

    def _set_value(self, exportedValue):
        self.desc.validateValue(exportedValue)
        # set individual child attribute values
        for key, value in exportedValue.items():
            self._value.get(key).value = value

    @Slot(str, result=Attribute)
    def childAttribute(self, key):
        """
        Get child attribute by name or None if none was found.

        Args:
            key (str): the name of the child attribute

        Returns:
            Attribute: the child attribute or None
        """
        try:
            return self._value.get(key)
        except KeyError:
            return None

    def uid(self, uidIndex):
        uids = []
        for k, v in self._value.items():
            if uidIndex in v.desc.uid:
                uids.append(v.uid(uidIndex))
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
        else:
            return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items() if not attr.isDefault}

    def getValueStr(self):
        # sort values based on child attributes group description order
        sortedSubValues = [self._value.get(attr.name).getValueStr() for attr in self.attributeDesc.groupDesc]
        return self.attributeDesc.joinChar.join(sortedSubValues)

    # Override value property
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)
