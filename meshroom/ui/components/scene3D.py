from math import acos, pi, sqrt

from PySide2.QtCore import QObject, Slot, QSize, Signal, QPointF
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtGui import QVector3D, QQuaternion, QVector2D

from meshroom.ui.utils import makeProperty

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


class TrackballController(QObject):
    """
    Trackball-like camera controller.
    Based on the C++ version from https://github.com/cjmdaixi/Qt3DTrackball
    """

    _windowSize = QSize()
    _camera = None
    _trackballSize = 1.0
    _rotationSpeed = 5.0

    def projectToTrackball(self, screenCoords):
        sx = screenCoords.x()
        sy = self._windowSize.height() - screenCoords.y()
        p2d = QVector2D(sx / self._windowSize.width() - 0.5, sy / self._windowSize.height() - 0.5)
        z = 0.0
        r2 = pow(self._trackballSize, 2)
        lengthSquared = p2d.lengthSquared()
        if lengthSquared <= r2 * 0.5:
            z = sqrt(r2 - lengthSquared)
        else:
            z = r2 * 0.5 / p2d.length()
        return QVector3D(p2d.x(), p2d.y(), z)

    @staticmethod
    def clamp(x):
        return max(-1, min(x, 1))

    def createRotation(self, firstPoint, nextPoint):
        lastPos3D = self.projectToTrackball(firstPoint).normalized()
        currentPos3D = self.projectToTrackball(nextPoint).normalized()
        angle = acos(self.clamp(QVector3D.dotProduct(currentPos3D, lastPos3D)))
        direction = QVector3D.crossProduct(currentPos3D, lastPos3D)
        return angle, direction

    @Slot(QPointF, QPointF, float)
    def rotate(self, lastPosition, currentPosition, dt):
        angle, direction = self.createRotation(lastPosition, currentPosition)
        rotatedAxis = self._camera.transform().rotation().rotatedVector(direction)
        angle *= self._rotationSpeed * dt
        self._camera.rotateAboutViewCenter(QQuaternion.fromAxisAndAngle(rotatedAxis, angle * pi * 180))

    windowSizeChanged = Signal()
    windowSize = makeProperty(QSize, '_windowSize', windowSizeChanged)
    cameraChanged = Signal()
    camera = makeProperty(Qt3DRender.QCamera, '_camera', cameraChanged)
    trackballSizeChanged = Signal()
    trackballSize = makeProperty(float, '_trackballSize', trackballSizeChanged)
    rotationSpeedChanged = Signal()
    rotationSpeed = makeProperty(float, '_rotationSpeed', rotationSpeedChanged)
