from PySide2.QtCore import QSettings

import meshroom
from meshroom.common import BaseObject, Property, Variant, VariantList, Signal, ListModel, Slot
from meshroom.core import nodesDesc
from meshroom.core.attribute import attributeFactory


class Preferences(BaseObject):
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
            nodesDict[g] = ListModel(parent=self)
            for a in settings.childKeys():
                if a != "__placeholder__":
                    value = settings.value(a)
                    desc = meshroom.core.nodesDesc[g].inputs
                    for d in desc:
                        if d._name == a:
                            attributeDesc = d
                            break
                    nodesDict[g].append(attributeFactory(attributeDesc, value, False))
            settings.endGroup()
        return nodesDict

    def getAttributeOverrides(self, nodeName):
        try:
            return self._attributes()[nodeName]
        except KeyError:
            return []

    @Slot(str)
    def addNodeOverride(self, nodeName):
        settings = self.getAttributeSettings()
        settings.beginGroup(nodeName)
        settings.setValue("__placeholder__", 0)
        self.attributeOverridesChanged.emit()

    @Slot(str)
    def removeNodeOverride(self, nodeName):
        settings = self.getAttributeSettings(nodeName)
        settings.remove("")
        settings.endGroup()
        self.attributeOverridesChanged.emit()

    def getUnusedNodes(self):
        unusedNodes = []
        usedNodes = self._attributes().keys()
        for n in nodesDesc.keys():
            if n not in usedNodes:
                unusedNodes.append(n)
        return unusedNodes

    @Slot(str, str, Variant)
    def addAttributeOverride(self, nodeName, attributeName, value):
        settings = self.getAttributeSettings(nodeName)
        settings.setValue(attributeName, value)
        self.attributeOverridesChanged.emit()

    @Slot(str, str)
    def removeAttributeOverride(self, nodeName, attributeName):
        settings = self.getAttributeSettings(nodeName)
        settings.remove(attributeName)
        self.attributeOverridesChanged.emit()

    @Slot(str, result=VariantList)
    def getUnusedAttributes(self, nodeName):
        unusedAttributes = []
        usedAttributes = [ a._name for a in self.getAttributeOverrides(nodeName) ]
        try:
            for a in nodesDesc[nodeName].inputs:
                if a._name not in usedAttributes:
                    unusedAttributes.append(a)
        except KeyError:
            return []
        return unusedAttributes

    attributeOverridesChanged = Signal()
    attributeOverrides = Property(Variant, _attributes, notify=attributeOverridesChanged)
    unusedNodes = Property(VariantList, getUnusedNodes, notify=attributeOverridesChanged)
