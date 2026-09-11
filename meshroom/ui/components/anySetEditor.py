# -*- coding: utf-8 -*-

"""
AnySet attributes editor: Provide list model and helper to edit a AnySet attribute items
"""

from PySide6.QtCore import (
    QObject,
    Slot,
    Signal,
    Property,
    QAbstractListModel,
    Qt,
    QModelIndex
)


EXPOSED_ATTR_TYPES = ["StringParam", "File", "IntParam", "FloatParam", "BoolParam"]


class AttributesSetModel(QAbstractListModel):
    TypeRole = Qt.UserRole + 1         # Attribute type
    NameRole = Qt.UserRole + 2         # Attribute name
    LabelRole = Qt.UserRole + 3        # Attribute label
    DescriptionRole = Qt.UserRole + 4  # Attribute description
    ValueRole = Qt.UserRole + 5        # Attribute value
    ObjectRole = Qt.UserRole + 6       # Attribute value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def roleNames(self):
        return {
            self.TypeRole: b"type",
            self.NameRole: b"name",
            self.LabelRole: b"label",
            self.DescriptionRole: b"description",
            self.ValueRole: b"value",
            self.ObjectRole: b"attributeObject",
        }

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None
        item = self._items[index.row()]
        if role == self.TypeRole:
            return item.get("type", "String")
        if role == self.NameRole:
            return item.get("name", "")
        if role == self.LabelRole:
            return item.get("label", "")
        if role == self.DescriptionRole:
            return item.get("description", "")
        if role == self.ValueRole:
            return item.get("value", "")
        if role == self.ObjectRole:
            return item.get("attributeObject", "")
        return None

    def reset(self, items):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def appendItem(self, item):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()

    def removeByName(self, name):
        for i, item in enumerate(self._items):
            if item.get("name") == name:
                self.beginRemoveRows(QModelIndex(), i, i)
                del self._items[i]
                self.endRemoveRows()
                return True
        return False


class NodeAttributeEditor(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._node = None
        self._attribute = None
        self._model = AttributesSetModel(self)

    def refresh(self):
        """Reload the model from the node's current inputs."""
        if self._node is None:
            self._model.reset([])
        else:
            self._model.reset(self.listInputs())
        self.inputsChanged.emit()
 
    def getNode(self):
        return self._node
 
    def setNode(self, node):
        if self._node is node:
            return
        self._node = node
        self.nodeChanged.emit()
        self.refresh()

    def getAttribute(self):
        return self._attribute

    def setAttribute(self, attribute):
        if self._attribute is attribute:
            return
        self._attribute = attribute
        self.attributeChanged.emit()
        self.refresh()

    @Slot(str, str, str, str, str)
    def addInput(self, attrType, name, label, description, value):
        """Add a new input attribute on the node using params dict."""
        if not name:
            self.errorOccurred.emit("Input name cannot be empty")
            return
        params = {
            "type": attrType,
            "name": name,
            "label": label,
            "description": description,
            "value": value,
        }
        try:
            insertIndex = len(list(self._attribute._value))
            self._attribute.insertAttribute(params, index=insertIndex)
            self._model.appendItem(params)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @Slot(str)
    def removeInput(self, inputName):
        """Remove the input attribute named inputName from the node."""
        try:
            for attr in list(self._attribute._value):
                if attr.name == inputName:
                    self._attribute.removeAttribute(attr)
            self._model.removeByName(inputName)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    def listInputs(self):
        """List inputs (build the list model displayed in the UI)."""
        inputs = list(self._attribute.value)
        inputsParams = []
        for i in range(len(inputs)):
            input_ = inputs[i]
            inputParams = {
                "type": input_._desc.__class__.__name__,
                "name": input_.name,
                "label": input_.label,
                "description": input_._desc.description,
                "value": input_.value,
                "attributeObject": input_,
            }
            inputsParams.append(inputParams)
        return inputsParams

    attrTypes = Property(list, lambda _: EXPOSED_ATTR_TYPES, constant=True)
    inputsChanged = Signal()
    errorOccurred = Signal(str)
    nodeChanged = Signal()
    node = Property(QObject, getNode, setNode, notify=nodeChanged)
    attributeChanged = Signal()
    attribute = Property(QObject, getAttribute, setAttribute, notify=attributeChanged)
    inputsModel = Property(QObject, lambda self: self._model, constant=True)
