from PySide2.QtCore import QObject, Slot, Signal, Property, QSettings

import meshroom
from meshroom.common.qt import QObjectListModel
from meshroom.core.attribute import attributeFactory


class Preferences(QObject):
    """ Manage Preferences. """

    def __init__(self, parent=None):
        super(Preferences, self).__init__(parent)

    def getAttributeSettings(self, nodeName=None):
        settings = QSettings()
        settings.beginGroup("NodeAttributeOverrides")
        if nodeName:
            settings.beginGroup(nodeName)
        return settings

    def _attributes(self):
        nodesDict = {}
        settings = self.getAttributeSettings()
        for g in settings.childGroups():
            settings.beginGroup(g)
            for a in settings.childKeys():
                value = settings.value(a)
                if not g in nodesDict:
                    nodesDict[g] = QObjectListModel(parent=self)
                desc = meshroom.core.nodesDesc[g].inputs
                for d in desc:
                    if d._name == a:
                        attributeDesc = d
                        break
                nodesDict[g].append(attributeFactory(attributeDesc, value, False))
        return nodesDict

    @Slot(str)
    def addNodeOverride(self, nodeName):
        settings = self.getAttributeSettings()
        settings.beginGroup(nodeName)
        settings.sync()
        self.attributeOverridesChanged.emit()

    @Slot(str)
    def removeNodeOverride(self, nodeName):
        settings = self.getAttributeSettings(nodeName)
        settings.remove("")
        settings.endGroup()
        self.attributeOverridesChanged.emit()

    @Slot(str, str, "QVariant")
    def addAttributeOverride(self, nodeName, attributeName, value):
        print(nodeName, attributeName, str(value))
        settings = self.getAttributeSettings(nodeName)
        settings.setValue(attributeName, value)
        self.attributeOverridesChanged.emit()

    @Slot(str, str)
    def removeAttributeOverride(self, nodeName, attributeName):
        settings = self.getAttributeSettings(nodeName)
        settings.remove(attributeName)
        self.attributeOverridesChanged.emit()

    attributeOverridesChanged = Signal()
    attributeOverrides = Property("QVariant", _attributes, notify=attributeOverridesChanged)
