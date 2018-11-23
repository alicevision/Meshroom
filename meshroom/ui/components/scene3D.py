from PySide2.QtCore import QObject, Slot
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender


class Scene3DHelper(QObject):

    @Slot(Qt3DCore.QEntity, str, result="QVariantList")
    def findChildrenByProperty(self, entity, propertyName):
        """ Recursively get all children of an entity that have a property named 'propertyName'. """
        children = []
        for child in entity.childNodes():
            try:
                if child.metaObject().indexOfProperty(propertyName) != -1:
                    children.append(child)
            except RuntimeError:
                continue
            children += self.findChildrenByProperty(child, propertyName)
        return children

    @Slot(Qt3DCore.QEntity, Qt3DCore.QComponent)
    def addComponent(self, entity, component):
        """ Adds a component to an entity. """
        entity.addComponent(component)

    @Slot(Qt3DCore.QEntity, Qt3DCore.QComponent)
    def removeComponent(self, entity, component):
        """ Removes a component from an entity. """
        entity.removeComponent(component)

    @Slot(Qt3DCore.QEntity, result=int)
    def vertexCount(self, entity):
        """ Return vertex count based on children QGeometryRenderer 'vertexCount'."""
        return sum([renderer.vertexCount() for renderer in entity.findChildren(Qt3DRender.QGeometryRenderer)])

    @Slot(Qt3DCore.QEntity, result=int)
    def faceCount(self, entity):
        """ Returns face count based on children QGeometry buffers size."""
        count = 0
        for geo in entity.findChildren(Qt3DRender.QGeometry):
            count += sum([attr.count() for attr in geo.attributes() if attr.name() == "vertexPosition"])
        return count / 3
