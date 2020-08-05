from meshroom.common.qt import QObjectListModel

from PySide2.QtCore import QObject, Slot, Signal, Property
from PySide2.QtCharts import QtCharts

import csv
import os

class CsvData(QObject):
    """
    Store data from a CSV file
    """
    def __init__(self):
        super(CsvData, self).__init__()
        self._filepath = ""
        self._data = QObjectListModel(parent=self)  # List of CsvColumn
        self._ready = False

    @Slot(int, result=QObject)
    def getColumn(self, index):
        return self._data.at(index)

    def getFilepath(self):
        return self._filepath

    def setFilepath(self, filepath):
        if self._filepath == filepath:
            return
        self._filepath = filepath
        self.updateData()
        self.filepathChanged.emit()

    def setReady(self, ready):
        if self._ready == ready:
            return
        self._ready = ready
        self.readyChanged.emit()

    def updateData(self):
        self.setReady(False)
        self._data.setObjectList(self.read())
        if not self._data.isEmpty():
            self.setReady(True)

    def read(self):
        """
        Read the CSV file and return a list containing CsvColumn objects
        """
        if not self._filepath or not self._filepath.endswith(".csv") or not os.path.isfile(self._filepath):
            return []

        csvRows = []
        with open(self._filepath, "r") as fp:
            reader = csv.reader(fp)
            for row in reader:
                csvRows.append(row)

        dataList = []

        # Create the objects in dataList
        # with the first line elements as objects' title
        for elt in csvRows[0]:
            dataList.append(CsvColumn(elt))

        # Populate the content attribute
        for elt in csvRows[1:]:
            for idx, value in enumerate(elt):
                dataList[idx].appendValue(value)

        return dataList

    filepathChanged = Signal()
    filepath = Property(str, getFilepath, setFilepath, notify=filepathChanged)
    readyChanged = Signal()
    ready = Property(bool, lambda self: self._ready, notify=readyChanged)
    data = Property(QObject, lambda self: self._data, constant=True)


class CsvColumn(QObject):
    """
    Store content of a CSV column
    """
    def __init__(self, title=""):
        super(CsvColumn, self).__init__()
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
        """
        Fill XYSerie used for displaying QML Chart
        """
        if not serie:
            return
        serie.clear()
        for index, value in enumerate(self._content):
            serie.append(float(index), float(value))

    title = Property(str, lambda self: self._title, constant=True)
    content = Property("QStringList", lambda self: self._content, constant=True)