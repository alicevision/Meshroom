from math import acos, pi, sqrt, atan2, cos, sin, asin

from PySide6.QtCore import QObject, Slot, QSize, Signal, QPointF
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtGui import QVector3D, QQuaternion, QVector2D, QVector4D, QMatrix4x4

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
        for geo in entity.findChildren(Qt3DCore.QGeometry):
            count += sum([attr.count() for attr in geo.attributes() if attr.name() == "vertexPosition"])
        return count / 3

    @Slot(Qt3DCore.QEntity, result=int)
    def vertexColorCount(self, entity):
        count = 0
        for geo in entity.findChildren(Qt3DCore.QGeometry):
            count += sum([attr.count() for attr in geo.attributes() if attr.name() == "vertexColor"])
        return count


class TrackballController(QObject):
    """
    Trackball-like camera controller.
    Based on the C++ version from https://github.com/cjmdaixi/Qt3DTrackball
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._windowSize = QSize()
        self._camera = None
        self._trackballSize = 1.0
        self._rotationSpeed = 5.0

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
    camera = makeProperty(QObject, '_camera', cameraChanged)
    trackballSizeChanged = Signal()
    trackballSize = makeProperty(float, '_trackballSize', trackballSizeChanged)
    rotationSpeedChanged = Signal()
    rotationSpeed = makeProperty(float, '_rotationSpeed', rotationSpeedChanged)


class Transformations3DHelper(QObject):

    # ---------- Exposed to QML ---------- #

    @Slot(QVector3D, QVector3D, result=QQuaternion)
    def rotationBetweenAandB(self, A, B):

        A = A/A.length()
        B = B/B.length()

        # Get rotation matrix between 2 vectors
        v = QVector3D.crossProduct(A, B)
        s = v.length()
        c = QVector3D.dotProduct(A, B)
        return QQuaternion.fromAxisAndAngle(v / s, atan2(s, c) * 180 / pi)

    @Slot(QVector3D, result=QVector3D)
    def fromEquirectangular(self, vector):
        return QVector3D(cos(vector.x()) * sin(vector.y()), sin(vector.x()), cos(vector.x()) * cos(vector.y()))

    @Slot(QVector3D, result=QVector3D)
    def toEquirectangular(self, vector):
        return QVector3D(asin(vector.y()), atan2(vector.x(), vector.z()), 0)

    @Slot(QVector3D, QVector2D, QVector2D, result=QVector3D)
    def updatePanorama(self, euler, ptStart, ptEnd):

        delta = 1e-3

        #Get initial rotation
        qStart = QQuaternion.fromEulerAngles(euler.y(), euler.x(), euler.z())

        #Convert input to points on unit sphere
        vStart = self.fromEquirectangular(QVector3D(ptStart))
        vStartdY = self.fromEquirectangular(QVector3D(ptStart.x(), ptStart.y() + delta, 0))
        vEnd = self.fromEquirectangular(QVector3D(ptEnd))

        qAdd = QQuaternion.rotationTo(vStart, vEnd)


        #Get the 3D point on unit sphere which would correspond to the no rotation +X
        vCurrent = qAdd.rotatedVector(vStartdY)
        vIdeal = self.fromEquirectangular(QVector3D(ptEnd.x(), ptEnd.y() + delta, 0))

        #project on rotation plane
        lambdaEnd = 1 / QVector3D.dotProduct(vEnd, vCurrent)
        lambdaIdeal = 1 / QVector3D.dotProduct(vEnd, vIdeal)
        vPlaneCurrent = lambdaEnd * vCurrent
        vPlaneIdeal = lambdaIdeal * vIdeal

        #Get the directions
        rotStart = (vPlaneCurrent - vEnd).normalized()
        rotEnd = (vPlaneIdeal - vEnd).normalized()

        # Get rotation matrix between 2 vectors
        v = QVector3D.crossProduct(rotEnd, rotStart)
        s = QVector3D.dotProduct(v, vEnd)
        c = QVector3D.dotProduct(rotStart, rotEnd)
        angle = atan2(s, c) * 180 / pi

        qImage = QQuaternion.fromAxisAndAngle(vEnd, -angle)

        return (qImage * qAdd * qStart).toEulerAngles()

    @Slot(QVector3D, QVector2D, QVector2D, result=QVector3D)
    def updatePanoramaInPlane(self, euler, ptStart, ptEnd):

        delta = 1e-3

        #Get initial rotation
        qStart = QQuaternion.fromEulerAngles(euler.y(), euler.x(), euler.z())

        #Convert input to points on unit sphere
        vStart = self.fromEquirectangular(QVector3D(ptStart))
        vEnd = self.fromEquirectangular(QVector3D(ptEnd))

        #Get the 3D point on unit sphere which would correspond to the no rotation +X
        vIdeal = self.fromEquirectangular(QVector3D(ptStart.x(), ptStart.y() + delta, 0))

        #project on rotation plane
        lambdaEnd = 1 / QVector3D.dotProduct(vStart, vEnd)
        lambdaIdeal = 1 / QVector3D.dotProduct(vStart, vIdeal)
        vPlaneEnd = lambdaEnd * vEnd
        vPlaneIdeal = lambdaIdeal * vIdeal

        #Get the directions
        rotStart = (vPlaneEnd - vStart).normalized()
        rotEnd = (vPlaneIdeal - vStart).normalized()

        # Get rotation matrix between 2 vectors
        v = QVector3D.crossProduct(rotEnd, rotStart)
        s = QVector3D.dotProduct(v, vStart)
        c = QVector3D.dotProduct(rotStart, rotEnd)
        angle = atan2(s, c) * 180 / pi

        qAdd = QQuaternion.fromAxisAndAngle(vStart, angle)

        return (qAdd * qStart).toEulerAngles()

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

    @Slot(QVector3D, result=QVector3D)
    def convertRotationFromCV2GL(self, rotation):
        """ Convert rotation (euler angles) from Computer Vision
            to Computer Graphics coordinate system (like opengl).
        """
        M = QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), 180.0)

        quaternion = QQuaternion.fromEulerAngles(rotation)

        U = M * quaternion * M

        return U.toEulerAngles()
    
    @Slot(QVector3D, QVector3D, float, float, result=QVector3D)
    def getRotatedCameraViewVector(self, camereViewVector, cameraUpVector, pitch, yaw):
        """ Compute the rotated camera view vector with given pitch and yaw (in degrees).
            Args:
                camereViewVector (QVector3D): Camera view vector, the displacement from the camera position to its target
                cameraUpVector (QVector3D): Camera up vector, the direction the top of the camera is facing
                pitch (float): Rotation pitch (in degrees)
                yaw (float): Rotation yaw (in degrees)
            Returns:
                QVector3D: rotated camera view vector
        """
        cameraSideVector = QVector3D.crossProduct(camereViewVector, cameraUpVector)
        yawRot = QQuaternion.fromAxisAndAngle(cameraUpVector, yaw)
        pitchRot = QQuaternion.fromAxisAndAngle(cameraSideVector, pitch)
        return (yawRot * pitchRot).rotatedVector(camereViewVector)
    
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
