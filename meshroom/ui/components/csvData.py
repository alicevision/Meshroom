from meshroom.common.qt import QObjectListModel

from PySide6.QtCore import QObject, Slot, Signal, Property
from PySide6 import QtCharts

import csv
import os
import logging


class CsvData(QObject):
    """Store data from a CSV file."""
    def __init__(self, parent=None):
        """Initialize the object without any parameter."""
        super(CsvData, self).__init__(parent=parent)
        self._filepath = ""
        self._data = QObjectListModel(parent=self)  # List of CsvColumn
        self._ready = False
        self.filepathChanged.connect(self.updateData)

    @Slot(int, result=QObject)
    def getColumn(self, index):
        return self._data.at(index)

    @Slot(result=str)
    def getFilepath(self):
        return self._filepath

    @Slot(result=int)
    def getNbColumns(self):
        if self._ready:
            return len(self._data)
        else:
            return 0

    @Slot(str)
    def setFilepath(self, filepath):
        if self._filepath == filepath:
            return
        self.setReady(False)
        self._filepath = filepath
        self.filepathChanged.emit()

    def setReady(self, ready):
        if self._ready == ready:
            return
        self._ready = ready
        self.readyChanged.emit()

    @Slot()
    def updateData(self):
        self.setReady(False)
        self._data.clear()
        newColumns = self.read()
        if newColumns:
            self._data.setObjectList(newColumns)
            self.setReady(True)

    def read(self):
        """Read the CSV file and return a list containing CsvColumn objects."""
        if not self._filepath or not self._filepath.lower().endswith(".csv") or not os.path.isfile(self._filepath):
            return []

        dataList = []
        try:
            csvRows = []
            with open(self._filepath, "r") as fp:
                reader = csv.reader(fp)
                for row in reader:
                    csvRows.append(row)
            # Create the objects in dataList
            # with the first line elements as objects' title
            for elt in csvRows[0]:
                dataList.append(CsvColumn(elt)) # , parent=self._data
            # Populate the content attribute
            for elt in csvRows[1:]:
                for idx, value in enumerate(elt):
                    dataList[idx].appendValue(value)
        except Exception as e:
            logging.error("CsvData: Failed to load file: {}\n{}".format(self._filepath, str(e)))

        return dataList

    filepathChanged = Signal()
    filepath = Property(str, getFilepath, setFilepath, notify=filepathChanged)
    readyChanged = Signal()
    ready = Property(bool, lambda self: self._ready, notify=readyChanged)
    data = Property(QObject, lambda self: self._data, notify=readyChanged)
    nbColumns = Property(int, getNbColumns, notify=readyChanged)


class CsvColumn(QObject):
    """Store content of a CSV column."""
    def __init__(self, title="", parent=None):
        """Initialize the object with optional column title parameter."""
        super(CsvColumn, self).__init__(parent=parent)
        self._title = title
        self._content = []

    def appendValue(self, value):
        self._content.append(value)

    @Slot(result=str)
    def getFirst(self):
        if not self._content:
            return ""
        return self._content[0]

    @Slot(result=str)
    def getLast(self):
        if not self._content:
            return ""
        return self._content[-1]

    @Slot(QtCharts.QXYSeries)
    def fillChartSerie(self, serie):
        """Fill XYSerie used for displaying QML Chart."""
        if not serie:
            return
        serie.clear()
        for index, value in enumerate(self._content):
            serie.append(float(index), float(value))

    title = Property(str, lambda self: self._title, constant=True)
    content = Property("QStringList", lambda self: self._content, constant=True)
