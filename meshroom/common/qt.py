from PySide6 import QtCore, QtQml
import shiboken6


class QObjectListModel(QtCore.QAbstractListModel):
    """
    QObjectListModel provides a more powerful, but still easy to use, alternative to using
    QObjectList lists as models for QML views. As a QAbstractListModel, it has the ability to
    automatically notify the view of specific changes to the list, such as adding or removing
    items. At the same time it provides QList-like convenience functions such as append, at,
    and removeAt for easily working with the model from Python.
    """
    ObjectRole = QtCore.Qt.UserRole

    def __init__(self, keyAttrName='', parent=None):
        """ Constructs an object list model with the given parent. """
        super(QObjectListModel, self).__init__(parent)

        self._objects = list()      # Internal list of objects
        self._keyAttrName = keyAttrName
        self._objectByKey = {}
        self.roles = QtCore.QAbstractListModel.roleNames(self)
        self.roles[self.ObjectRole] = b"object"

        self.requestDeletion.connect(self.onRequestDeletion, QtCore.Qt.QueuedConnection)

    def roleNames(self):
        return self.roles

    def __iter__(self):
        """ Enables iteration over the list of objects. """
        return iter(self._objects)

    def keys(self):
        return self._objectByKey.keys()

    def items(self):
        return self._objectByKey.items()

    def __len__(self):
        return self.size()

    def __bool__(self):
        return self.size() > 0

    def __getitem__(self, index):
        """ Enables the [] operator.
        Only accepts index (integer).
        """
        return self._objects[index]

    def data(self, index, role):
        """ Returns data for the specified role, from the item with the
        given index. The only valid role is ObjectRole.

        If the view requests an invalid index or role, an invalid variant
        is returned.
        """
        if index.row() < 0 or index.row() >= len(self._objects):
            return None
        return self._objects[index.row()]

    def rowCount(self, parent):
        """ Returns the number of rows in the model. This value corresponds to the
        number of items in the model's internal object list.
        """
        return self.size()

    def objectList(self):
        """ Returns the object list used by the model to store data. """
        return self._objects

    def values(self):
        return self._objects

    def setObjectList(self, objects):
        """ Sets the model's internal objects list to objects. The model will
        notify any attached views that its underlying data has changed.
        """
        oldSize = self.size()
        self.beginResetModel()
        for obj in self._objects:
            self._dereferenceItem(obj)
        self._objects = objects
        for obj in self._objects:
            self._referenceItem(obj)
        self.endResetModel()
        self.dataChanged.emit(self.index(0), self.index(self.size() - 1), [])
        if self.size() != oldSize:
            self.countChanged.emit()

    # ######
    # BaseModel API
    # ######
    @property
    def objects(self):
        return self._objectByKey

    @QtCore.Slot(str, result=QtCore.QObject)
    def get(self, key):
        """
        :param key:
        :return: the value or None if not found
        """
        return self._objectByKey.get(key)

    @QtCore.Slot(str, result=QtCore.QObject)
    def getr(self, key):
        """
        Get or raise an error if the key does not exists.
        :param key:
        :return: the value
        """
        return self._objectByKey[key]

    def add(self, obj):
        self.append(obj)

    def pop(self, key):
        obj = self.get(key)
        self.remove(obj)
        return obj

    ############
    # List API #
    ############
    @QtCore.Slot(QtCore.QObject)
    def append(self, obj):
        """ Insert object at the end of the model. """
        self.extend([obj])

    def extend(self, iterable):
        """ Insert objects at the end of the model. """
        self.beginInsertRows(QtCore.QModelIndex(), self.size(), self.size() + len(iterable) - 1)
        [self._referenceItem(obj) for obj in iterable]
        self._objects.extend(iterable)
        self.endInsertRows()
        self.countChanged.emit()

    def insert(self, i, toInsert):
        """  Inserts object(s) at index position i in the model and notifies
        any views. If i is 0, the object is prepended to the model. If i
        is size(), the object is appended to the list.
        Accepts both QObject and list of QObjects.
        """
        if not isinstance(toInsert, list):
            toInsert = [toInsert]
        self.beginInsertRows(QtCore.QModelIndex(), i, i + len(toInsert) - 1)
        for obj in reversed(toInsert):
            self._referenceItem(obj)
            self._objects.insert(i, obj)
        self.endInsertRows()
        self.countChanged.emit()

    @QtCore.Slot(int, result=QtCore.QObject)
    def at(self, i):
        """ Return the object at index i. """
        return self._objects[i]

    def replace(self, i, obj):
        """ Replaces the item at index position i with object and
        notifies any views. i must be a valid index position in the list
        (i.e., 0 <= i < size()).
        """
        self._dereferenceItem(self._objects[i])
        self._referenceItem(obj)
        self._objects[i] = obj
        self.dataChanged.emit(self.index(i), self.index(i), [])

    def move(self, fromIndex, toIndex):
        """ Moves the item at index position from to index position to
        and notifies any views.
        This function assumes that both from and to are at least 0 but less than
        size(). To avoid failure, test that both from and to are at
        least 0 and less than size().
        """
        value = toIndex
        if toIndex > fromIndex:
            value += 1
        if not self.beginMoveRows(QtCore.QModelIndex(), fromIndex, fromIndex, QtCore.QModelIndex(), value):
            return
        self._objects.insert(toIndex, self._objects.pop(fromIndex))
        self.endMoveRows()

    def removeAt(self, i, count=1):
        """  Removes count number of items from index position i and notifies any views.
        i must be a valid index position in the model (i.e., 0 <= i < size()), as
        must as i + count - 1.
        """
        self.beginRemoveRows(QtCore.QModelIndex(), i, i + count - 1)
        for cpt in range(count):
            obj = self._objects.pop(i)
            self._dereferenceItem(obj)
        self.endRemoveRows()
        self.countChanged.emit()

    @QtCore.Slot(QtCore.QObject)
    def remove(self, obj):
        """ Removes the first occurrence of the given object. Raises a ValueError if not in list. """
        if not self.contains(obj):
            raise ValueError("QObjectListModel.remove(obj) : obj not in list")
        self.removeAt(self.indexOf(obj))

    def takeAt(self, i):
        """  Removes the item at index position i (notifying any views) and returns it.
        i must be a valid index position in the model (i.e., 0 <= i < size()).
        """
        self.beginRemoveRows(QtCore.QModelIndex(), i, i)
        obj = self._objects.pop(i)
        self._dereferenceItem(obj)
        self.endRemoveRows()
        self.countChanged.emit()
        return obj

    def clear(self):
        """ Removes all items from the model and notifies any views. """
        if not self._objects:
            return
        self.beginResetModel()
        for obj in self._objects:
            self._dereferenceItem(obj)
        self._objects = []
        self.endResetModel()
        self.countChanged.emit()

    def update(self, objects):
        self.extend(objects)

    def reset(self, objects):
        self.setObjectList(objects)

    @QtCore.Slot(QtCore.QObject, result=bool)
    def contains(self, obj):
        """ Returns true if the list contains an occurrence of object;
        otherwise returns false.
        """
        return obj in self._objects

    @QtCore.Slot(QtCore.QObject, result=int)
    def indexOf(self, matchObj, fromIndex=0, positive=True):
        """ Returns the index position of the first occurrence of object in
        the model, searching forward from index position from.
        If positive is True, will always return a positive index.
        """
        index = self._objects[fromIndex:].index(matchObj) + fromIndex
        if positive and index < 0:
            index += self.size()
        return index

    def lastIndexOf(self, matchObj, fromIndex=-1, positive=True):
        """    Returns the index position of the last occurrence of object in
        the list, searching backward from index position from. If
        from is -1 (the default), the search starts at the last item.
        If positive is True, will always return a positive index.
        """
        r = list(self._objects)
        r.reverse()
        index = - r[-fromIndex - 1:].index(matchObj) + fromIndex
        if positive and index < 0:
            index += self.size()
        return index

    def size(self):
        """ Returns the number of items in the model. """
        return len(self._objects)

    @QtCore.Slot(result=bool)
    def isEmpty(self):
        """ Returns true if the model contains no items; otherwise returns false. """
        return len(self._objects) == 0

    def _referenceItem(self, item):
        if not item.parent():
            # Take ownership of the object if not already parented
            item.setParent(self)
        if not self._keyAttrName:
            return
        key = getattr(item, self._keyAttrName, None)
        if key is None:
            return
        if key in self._objectByKey:
            raise ValueError("Object key {}:{} is not unique".format(self._keyAttrName, key))

        self._objectByKey[key] = item

    @QtCore.Slot(int, result=QtCore.QModelIndex)
    def index(self, row: int, column: int = 0, parent=QtCore.QModelIndex()):
        """ Returns the model index for the given row, column and parent index. """
        if parent.isValid() or column != 0:
            return QtCore.QModelIndex()
        if row < 0 or row >= self.size():
            return QtCore.QModelIndex()
        return self.createIndex(row, column, self._objects[row])

    def _dereferenceItem(self, item):
        # Ask for object deletion if parented to the model
        if shiboken6.isValid(item) and item.parent() == self:
            # delay deletion until the next event loop
            # This avoids warnings when the QML engine tries to evaluate (but should not)
            # an object that has already been deleted
            self.requestDeletion.emit(item)

        if not self._keyAttrName:
            return
        key = getattr(item, self._keyAttrName, None)
        if key is None:
            return
        assert key in self._objectByKey
        del self._objectByKey[key]

    def onRequestDeletion(self, item):
        item.deleteLater()

    countChanged = QtCore.Signal()
    count = QtCore.Property(int, size, notify=countChanged)

    requestDeletion = QtCore.Signal(QtCore.QObject)


class QTypedObjectListModel(QObjectListModel):
    """ Typed QObjectListModel that exposes T properties as roles """
    # TODO: handle notify signal to emit dataChanged signal

    def __init__(self, keyAttrName="name", T=QtCore.QObject, parent=None):
        super(QTypedObjectListModel, self).__init__(keyAttrName, parent)

        self._T = T
        blacklist = ["id", "index", "class", "model", "modelData"]

        self._metaObject = T.staticMetaObject
        propCount = self._metaObject.propertyCount()

        role = self.ObjectRole + 1
        for i in range(0, propCount):
            prop = self._metaObject.property(i)
            if not prop.name() in blacklist:
                self.roles[role] = prop.name()
                role += 1
            else:
                print("Reserved role name: " + prop.name())

    def data(self, index, role):
        obj = super(QTypedObjectListModel, self).data(index, self.ObjectRole)
        if role == self.ObjectRole:
            return obj
        if obj:
            return obj.property(self.roles[role])
        return None

    def roleForName(self, name):
        roles = [role for role, value in self.roles.items() if value == name]
        return roles[0] if roles else -1

    def _referenceItem(self, item):
        if item.staticMetaObject != self._metaObject:
            raise TypeError("Invalid object type: expected {}, got {}".format(
                self._metaObject.className(), item.staticMetaObject.className()))
        super(QTypedObjectListModel, self)._referenceItem(item)


class SortedModelByReference(QtCore.QSortFilterProxyModel):
    """ Sort a source model based on the ordered list (reference) of the same elements.
    This proxy is useful if the model needs to be sorted a certain way for a specific use.
    """
    def __init__(self, parent):
        super(SortedModelByReference, self).__init__(parent)
        self._reference = []

    def setReference(self, iterable):
        """ Set the reference ordered list """
        self._reference = iterable
        self.sort()

    def reference(self):
        return self._reference

    def lessThan(self, left, right):
        l = self.sourceModel().data(left, QObjectListModel.ObjectRole)
        r = self.sourceModel().data(right, QObjectListModel.ObjectRole)
        if l not in self._reference:
            return False
        if r not in self._reference:
            return True
        return self._reference.index(l) < self._reference.index(r)

    def sort(self):
        """ Sort the proxy and call invalidate() """
        super(SortedModelByReference, self).sort(0, QtCore.Qt.AscendingOrder)
        self.invalidate()


DictModel = QObjectListModel
ListModel = QObjectListModel
Slot = QtCore.Slot
Signal = QtCore.Signal
Property = QtCore.Property
BaseObject = QtCore.QObject
Variant = "QVariant"
VariantList = "QVariantList"
JSValue = QtQml.QJSValue
