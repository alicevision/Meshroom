from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt, Property, Signal, Slot


def objectAt(model, row):
    """
    Return the QObject at 'row' in a list model exposing its objects with an "object" role
    (such as QObjectListModel), or None if there is no such role.
    """
    for role, name in model.roleNames().items():
        if name == b"object":
            return model.data(model.index(row, 0), role)
    return None


class ObjectTableModel(QAbstractTableModel):
    """
    Table model built on top of a list model of row objects, in which each row object
    exposes a list model of cell objects through its "value" property.

    Each row of the source model is a row of the table, and each cell of a row is a column.
    The number of columns and their headers (the cells' "label") are given by the first row.
    """

    ObjectRole = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        # Whether a source change is being forwarded as a model reset
        self._resetting = False

    def roleNames(self):
        return {Qt.DisplayRole: b"display", self.ObjectRole: b"object"}

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid() or self._source is None:
            return 0
        return self._source.rowCount(QModelIndex())

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid() or self.rowCount() == 0:
            return 0
        cells = self._cells(self.rowObject(0))
        return cells.rowCount(QModelIndex()) if cells is not None else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, self.ObjectRole):
            return None
        return self._cellObject(index.row(), index.column())

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """ Return the label of the first row's cells for columns. Rows have no header data. """
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        cell = self._cellObject(0, section)
        return cell.property("label") if cell is not None else None

    @Slot(int, result=QObject)
    def rowObject(self, row):
        if row < 0 or row >= self.rowCount():
            return None
        return objectAt(self._source, row)

    def _cells(self, rowObject):
        if rowObject is None:
            return None
        return rowObject.property("value")

    def _cellObject(self, row, column):
        cells = self._cells(self.rowObject(row))
        if cells is None or column < 0 or column >= cells.rowCount(QModelIndex()):
            return None
        return objectAt(cells, column)

    def _emitHeaderChanged(self):
        if self.columnCount() > 0:
            self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount() - 1)

    # Forwarding of the source model's changes.
    # The columns are given by the first row, so the model is reset when the table
    # becomes empty or stops being empty.
    def _onRowsAboutToBeInserted(self, parent, first, last):
        self._resetting = self.rowCount() == 0
        if self._resetting:
            self.beginResetModel()
        else:
            self.beginInsertRows(QModelIndex(), first, last)

    def _onRowsInserted(self, parent, first, last):
        if self._resetting:
            self._resetting = False
            self.endResetModel()
            return
        self.endInsertRows()
        if first == 0:
            self._emitHeaderChanged()

    def _onRowsAboutToBeRemoved(self, parent, first, last):
        self._resetting = last - first + 1 == self.rowCount()
        if self._resetting:
            self.beginResetModel()
        else:
            self.beginRemoveRows(QModelIndex(), first, last)

    def _onRowsRemoved(self, parent, first, last):
        if self._resetting:
            self._resetting = False
            self.endResetModel()
            return
        self.endRemoveRows()
        if first == 0:
            self._emitHeaderChanged()

    def _onRowsAboutToBeMoved(self, sourceParent, first, last, destinationParent, destination):
        self.beginMoveRows(QModelIndex(), first, last, QModelIndex(), destination)

    def _onRowsMoved(self, sourceParent, first, last, destinationParent, destination):
        self.endMoveRows()
        self._emitHeaderChanged()

    def _onSourceDataChanged(self, topLeft, bottomRight, roles=None):
        if self.columnCount() > 0:
            self.dataChanged.emit(self.index(topLeft.row(), 0), self.index(bottomRight.row(), self.columnCount() - 1))

    def _sourceConnections(self):
        return [
            (self._source.rowsAboutToBeInserted, self._onRowsAboutToBeInserted),
            (self._source.rowsInserted, self._onRowsInserted),
            (self._source.rowsAboutToBeRemoved, self._onRowsAboutToBeRemoved),
            (self._source.rowsRemoved, self._onRowsRemoved),
            (self._source.rowsAboutToBeMoved, self._onRowsAboutToBeMoved),
            (self._source.rowsMoved, self._onRowsMoved),
            (self._source.modelAboutToBeReset, self.beginResetModel),
            (self._source.modelReset, self.endResetModel),
            (self._source.dataChanged, self._onSourceDataChanged),
            (self._source.destroyed, self._onSourceDestroyed),
        ]

    def _onSourceDestroyed(self):
        # The source can't be disconnected anymore, only forget it
        self.beginResetModel()
        self._source = None
        self.endResetModel()
        self.sourceChanged.emit()

    def getSource(self):
        return self._source

    def setSource(self, source):
        if source == self._source:
            return
        self.beginResetModel()
        if self._source is not None:
            for signal, slot in self._sourceConnections():
                signal.disconnect(slot)
        self._source = source
        if self._source is not None:
            for signal, slot in self._sourceConnections():
                signal.connect(slot)
        self.endResetModel()
        self.sourceChanged.emit()

    sourceChanged = Signal()
    source = Property(QObject, getSource, setSource, notify=sourceChanged)
