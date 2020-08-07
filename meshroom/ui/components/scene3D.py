from math import acos, pi, sqrt

from PySide2.QtCore import QObject, Slot, QSize, Signal, QPointF
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtGui import QVector3D, QQuaternion, QVector2D, QVector4D, QMatrix4x4

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

    @Slot(Qt3DCore.QEntity, result=int)
    def vertexColorCount(self, entity):
        count = 0
        for geo in entity.findChildren(Qt3DRender.QGeometry):
            count += sum([attr.count() for attr in geo.attributes() if attr.name() == "vertexColor"])
        return count


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


class Transformations3DHelper(QObject):

    # ---------- Exposed to QML ---------- #

    @Slot(QVector4D, Qt3DRender.QCamera, QSize, result=QVector2D)
    def pointFromWorldToScreen(self, point, camera, windowSize):
        """ Compute the Screen point corresponding to a World Point.
            Args:
                point (QVector4D): point in world coordinates
                camera (QCamera): camera viewing the scene
                windowSize (QSize): size of the Scene3D window
            Returns:
                QVector2D: point in screen coordinates
        """
        # Transform the point from World Coord to Normalized Device Coord
        viewMatrix = camera.transform().matrix().inverted()
        projectedPoint = (camera.projectionMatrix() * viewMatrix[0]).map(point)
        projectedPoint2D = QVector2D(
            projectedPoint.x()/projectedPoint.w(), 
            projectedPoint.y()/projectedPoint.w()
        )

        # Transform the point from Normalized Device Coord to Screen Coord
        screenPoint2D = QVector2D(
            int((projectedPoint2D.x() + 1) * windowSize.width() / 2),
            int((projectedPoint2D.y() - 1) * windowSize.height() / -2)
        )

        return screenPoint2D

    @Slot(Qt3DCore.QTransform, QMatrix4x4, QMatrix4x4, QMatrix4x4, QVector3D)
    def relativeLocalTranslate(self, transformQtInstance, initialPosMat, initialRotMat, initialScaleMat, translateVec):
        """ Translate the QTransform in its local space relatively to an initial state.
            Args:
                transformQtInstance (QTransform): reference to the Transform to modify
                initialPosMat (QMatrix4x4): initial position matrix
                initialRotMat (QMatrix4x4): initial rotation matrix
                initialScaleMat (QMatrix4x4): initial scale matrix
                translateVec (QVector3D): vector used for the local translation
        """
        # Compute the translation transformation matrix 
        translationMat = QMatrix4x4()
        translationMat.translate(translateVec)

        # Compute the new model matrix (POSITION * ROTATION * TRANSLATE * SCALE) and set it to the Transform
        mat = initialPosMat * initialRotMat * translationMat * initialScaleMat
        transformQtInstance.setMatrix(mat)

    @Slot(Qt3DCore.QTransform, QMatrix4x4, QQuaternion, QMatrix4x4, QVector3D, int)
    def relativeLocalRotate(self, transformQtInstance, initialPosMat, initialRotQuat, initialScaleMat, axis, degree):
        """ Rotate the QTransform in its local space relatively to an initial state.
            Args:
                transformQtInstance (QTransform): reference to the Transform to modify
                initialPosMat (QMatrix4x4): initial position matrix
                initialRotQuat (QQuaternion): initial rotation quaternion
                initialScaleMat (QMatrix4x4): initial scale matrix
                axis (QVector3D): axis to rotate around
                degree (int): angle of rotation in degree
        """
        # Compute the transformation quaternion from axis and angle in degrees
        transformQuat = QQuaternion.fromAxisAndAngle(axis, degree)

        # Compute the new rotation quaternion and then calculate the matrix
        newRotQuat = initialRotQuat * transformQuat # Order is important
        newRotationMat = self.quaternionToRotationMatrix(newRotQuat)

        # Compute the new model matrix (POSITION * NEW_COMPUTED_ROTATION * SCALE) and set it to the Transform
        mat = initialPosMat * newRotationMat * initialScaleMat
        transformQtInstance.setMatrix(mat)

    @Slot(Qt3DCore.QTransform, QMatrix4x4, QMatrix4x4, QMatrix4x4, QVector3D)
    def relativeLocalScale(self, transformQtInstance, initialPosMat, initialRotMat, initialScaleMat, scaleVec):
        """ Scale the QTransform in its local space relatively to an initial state.
            Args:
                transformQtInstance (QTransform): reference to the Transform to modify
                initialPosMat (QMatrix4x4): initial position matrix
                initialRotMat (QMatrix4x4): initial rotation matrix
                initialScaleMat (QMatrix4x4): initial scale matrix
                scaleVec (QVector3D): vector used for the relative scale
        """
        # Make a copy of the scale matrix (otherwise, it is a reference and it does not work as expected)
        scaleMat = self.copyMatrix4x4(initialScaleMat)

        # Update the scale matrix copy (X then Y then Z) with the scaleVec values
        scaleVecTuple = scaleVec.toTuple()
        for i in range(3):
            currentRow = list(scaleMat.row(i).toTuple()) # QVector3D does not implement [] operator or easy way to access value by index so this little hack is required
            value = currentRow[i] + scaleVecTuple[i]
            value = value if value >= 0 else -value # Make sure to have only positive scale (because negative scale can make issues with matrix decomposition)
            currentRow[i] = value

            scaleMat.setRow(i, QVector3D(currentRow[0], currentRow[1], currentRow[2])) # Apply the new row to the scale matrix

        # Compute the new model matrix (POSITION * ROTATION * SCALE) and set it to the Transform
        mat = initialPosMat * initialRotMat * scaleMat
        transformQtInstance.setMatrix(mat)

    @Slot(QMatrix4x4, result="QVariant")
    def modelMatrixToMatrices(self, modelMat):
        """ Decompose a model matrix into individual matrices.
            Args:
                modelMat (QMatrix4x4): model matrix to decompose
            Returns:
                QVariant: object containing position, rotation and scale matrices + rotation quaternion
        """
        decomposition = self.decomposeModelMatrix(modelMat)

        posMat = QMatrix4x4()
        posMat.translate(decomposition.get("translation"))

        rotMat = self.quaternionToRotationMatrix(decomposition.get("quaternion"))

        scaleMat = QMatrix4x4()
        scaleMat.scale(decomposition.get("scale"))

        return {"position": posMat, "rotation": rotMat, "scale": scaleMat, "quaternion": decomposition.get("quaternion")}

    @Slot(QVector3D, QVector3D, QVector3D, result=QMatrix4x4)
    def computeModelMatrixWithEuler(self, translation, rotation, scale):
        """ Compute a model matrix from three Vector3D.
            Args:
                translation (QVector3D): position in space (x, y, z)
                rotation (QVector3D): Euler angles in degrees (x, y, z)
                scale (QVector3D): scale of the object (x, y, z)
            Returns:
                QMatrix4x4: corresponding model matrix
        """
        posMat = QMatrix4x4()
        posMat.translate(translation)

        quaternion = QQuaternion.fromEulerAngles(rotation)
        rotMat = self.quaternionToRotationMatrix(quaternion)

        scaleMat = QMatrix4x4()
        scaleMat.scale(scale)

        modelMat = posMat * rotMat * scaleMat

        return modelMat

    @Slot(QVector3D, QMatrix4x4, Qt3DRender.QCamera, QSize, result=float)
    def computeScaleUnitFromModelMatrix(self, axis, modelMat, camera, windowSize):
        """ Compute the length of the screen projected vector axis unit transformed by the model matrix.
            Args:
                axis (QVector3D): chosen axis ((1,0,0) or (0,1,0) or (0,0,1))
                modelMat (QMatrix4x4): model matrix used for the transformation
                camera (QCamera): camera viewing the scene
                windowSize (QSize): size of the window in pixels
            Returns:
                float: length (in pixels)
        """
        decomposition = self.decomposeModelMatrix(modelMat)

        posMat = QMatrix4x4()
        posMat.translate(decomposition.get("translation"))

        rotMat = self.quaternionToRotationMatrix(decomposition.get("quaternion"))

        unitScaleModelMat = posMat * rotMat * QMatrix4x4()

        worldCenterPoint = unitScaleModelMat.map(QVector4D(0,0,0,1))
        worldAxisUnitPoint = unitScaleModelMat.map(QVector4D(axis.x(),axis.y(),axis.z(),1))
        screenCenter2D = self.pointFromWorldToScreen(worldCenterPoint, camera, windowSize)
        screenAxisUnitPoint2D = self.pointFromWorldToScreen(worldAxisUnitPoint, camera, windowSize)

        screenVector = QVector2D(screenAxisUnitPoint2D.x() - screenCenter2D.x(), -(screenAxisUnitPoint2D.y() - screenCenter2D.y()))

        value = screenVector.length()
        return value if (value and value > 10) else 10  # Threshold to avoid problems in extreme case

    # ---------- "Private" Methods ---------- #

    def copyMatrix4x4(self, mat):
        """ Make a deep copy of a QMatrix4x4. """
        newMat = QMatrix4x4()
        for i in range(4):
            newMat.setRow(i, mat.row(i))
        return newMat

    def decomposeModelMatrix(self, modelMat):
        """ Decompose a model matrix into individual component.
            Args:
                modelMat (QMatrix4x4): model matrix to decompose
            Returns:
                QVariant: object containing translation and scale vectors + rotation quaternion
        """
        translation = modelMat.column(3).toVector3D()
        quaternion = QQuaternion.fromDirection(modelMat.column(2).toVector3D(), modelMat.column(1).toVector3D())
        scale = QVector3D(modelMat.column(0).length(), modelMat.column(1).length(), modelMat.column(2).length())

        return {"translation": translation, "quaternion": quaternion, "scale": scale}

    def quaternionToRotationMatrix(self, q):
        """ Return a rotation matrix from a quaternion. """
        rotMat3x3 = q.toRotationMatrix()
        return QMatrix4x4(
            rotMat3x3(0, 0), rotMat3x3(0, 1), rotMat3x3(0, 2), 0,
            rotMat3x3(1, 0), rotMat3x3(1, 1), rotMat3x3(1, 2), 0,
            rotMat3x3(2, 0), rotMat3x3(2, 1), rotMat3x3(2, 2), 0,
            0,               0,               0,               1
        )
