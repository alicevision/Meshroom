import struct
from math import pi, atan2, cos, sin, asin, degrees, radians, tan

from PySide6.QtCore import QObject, Slot, QSize, Signal, QPointF, QByteArray
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
        """ Return vertex count based on children QGeometryRenderer 'vertexCount'. """
        return sum([renderer.vertexCount() for renderer in entity.findChildren(Qt3DRender.QGeometryRenderer)])

    @Slot(Qt3DCore.QEntity, result=int)
    def faceCount(self, entity):
        """ Returns face count based on children QGeometry buffers size. """
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

    @Slot(Qt3DCore.QEntity)
    def ensureNormals(self, entity):
        """
        Add default normal attributes to geometries that don't have them.
        This prevents Metal RHI pipeline crashes when built-in Qt3D materials
        (which require vertexNormal) are used with meshes lacking normals.
        """
        for geo in entity.findChildren(Qt3DCore.QGeometry):
            hasNormals = any(attr.name() == "vertexNormal" for attr in geo.attributes())
            if hasNormals:
                continue

            # Find the vertexPosition attribute to get vertex count
            posAttr = None
            for attr in geo.attributes():
                if attr.name() == "vertexPosition":
                    posAttr = attr
                    break
            if not posAttr:
                continue

            vertexCount = posAttr.count()

            # Create a buffer filled with (0, 1, 0) default normals
            normalData = QByteArray(struct.pack('<fff', 0.0, 1.0, 0.0) * vertexCount)
            normalBuffer = Qt3DCore.QBuffer(geo)
            normalBuffer.setData(normalData)

            # Create the normal attribute
            normalAttr = Qt3DCore.QAttribute(geo)
            normalAttr.setName("vertexNormal")
            normalAttr.setVertexBaseType(Qt3DCore.QAttribute.Float)
            normalAttr.setVertexSize(3)
            normalAttr.setAttributeType(Qt3DCore.QAttribute.VertexAttribute)
            normalAttr.setBuffer(normalBuffer)
            normalAttr.setByteStride(3 * 4)  # 3 floats * 4 bytes
            normalAttr.setByteOffset(0)
            normalAttr.setCount(vertexCount)

            geo.addAttribute(normalAttr)


class TurntableCameraController(QObject):
    """
    Turntable-like camera controller.

    The camera orbits around its view center: horizontal mouse moves yaw it around the world
    up axis, vertical ones pitch it around its own right axis. No rotation is ever applied
    around the view axis, so the camera never rolls and the horizon - hence the ground grid -
    always stays level.

    Panning and zooming are expressed in pixels as well, so that every manipulation is
    frame rate independent and keeps the point grabbed by the cursor under the cursor.
    """

    # World up axis, around which the camera yaws: the 3D viewer scene is Y-up.
    upAxis = QVector3D(0.0, 1.0, 0.0)
    # Keep the camera away from the poles: an up vector perfectly aligned
    # with the view direction would make the view matrix degenerate.
    maxElevation = 89.9
    # Distance to the view center is multiplied by this factor for each zoom step
    # (one mouse wheel notch). Being multiplicative, zooming in then back out by
    # the same number of steps restores the initial distance exactly.
    zoomFactor = 0.8
    # Zoom steps applied by a drag over the whole viewport height.
    dragZoomSteps = 8.0
    # Never keep less than this fraction of the distance to the view center in a single zoom:
    # getting arbitrarily close would make the following translations collapse to zero.
    minZoomRatio = 0.1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._windowSize = QSize()
        self._camera = None
        self._rotationSpeed = 200.0
        self._zoomToCursor = True

    @staticmethod
    def clamp(x, minValue=-1.0, maxValue=1.0):
        return max(minValue, min(x, maxValue))

    def orbitOffset(self):
        """
        Offset from the view center to the camera, and its length.
        Returns (None, 0.0) when the controller has nothing usable to manipulate.
        """
        if self._camera is None or self._windowSize.isEmpty():
            return None, 0.0
        offset = self._camera.position() - self._camera.viewCenter()
        distance = offset.length()
        if distance < 1e-6:
            return None, 0.0
        return offset, distance

    def screenAxes(self, viewDirection):
        """ Camera right and up axes, orthonormalized against the given view direction. """
        right = QVector3D.crossProduct(viewDirection, self._camera.upVector()).normalized()
        return right, QVector3D.crossProduct(right, viewDirection).normalized()

    def worldPerPixel(self, distance):
        """ World size, in the plane passing through the view center, covered by one viewport pixel. """
        return 2.0 * distance * tan(radians(self._camera.fieldOfView()) * 0.5) / self._windowSize.height()

    def pitchAxis(self, viewDirection):
        """ Screen-horizontal axis to pitch around: orthogonal to both the view direction and the up axis. """
        axis = QVector3D.crossProduct(viewDirection, self.upAxis)
        if axis.length() < 1e-6:
            # Looking straight up or down: fall back on the camera's own right axis.
            axis = self._camera.transform().rotation().rotatedVector(QVector3D(1.0, 0.0, 0.0))
        return axis.normalized()

    def levelledUpVector(self, viewDirection):
        """ Roll-free up vector: the up axis made orthogonal to the given view direction. """
        up = self.upAxis - viewDirection * QVector3D.dotProduct(self.upAxis, viewDirection)
        return up.normalized()

    @Slot(QPointF, QPointF)
    def rotate(self, lastPosition, currentPosition):
        """
        Orbit the camera around its view center, following the mouse drag
        from 'lastPosition' to 'currentPosition' (both in pixels).
        """
        offset, distance = self.orbitOffset()
        if offset is None:
            return

        # Normalize both drags by the window height, so that the same pixel distance
        # always yields the same rotation whatever the viewport aspect ratio:
        # dragging over the viewport height rotates the camera by 'rotationSpeed' degrees.
        dx = (currentPosition.x() - lastPosition.x()) / self._windowSize.height()
        dy = (currentPosition.y() - lastPosition.y()) / self._windowSize.height()

        viewCenter = self._camera.viewCenter()
        direction = offset / distance  # From the view center to the camera

        # Horizontal drag: yaw around the world up axis.
        yaw = QQuaternion.fromAxisAndAngle(self.upAxis, -dx * self._rotationSpeed)

        # Vertical drag: raise/lower the camera, without ever crossing the poles.
        elevation = degrees(asin(self.clamp(QVector3D.dotProduct(direction, self.upAxis))))
        deltaElevation = self.clamp(elevation + dy * self._rotationSpeed,
                                    -self.maxElevation, self.maxElevation) - elevation
        pitch = QQuaternion.fromAxisAndAngle(self.pitchAxis(-direction), -deltaElevation)

        direction = yaw.rotatedVector(pitch.rotatedVector(direction))
        self._camera.setPosition(viewCenter + direction * distance)
        self._camera.setUpVector(self.levelledUpVector(-direction))

    @Slot(QPointF, QPointF)
    def pan(self, lastPosition, currentPosition):
        """
        Translate the camera and its view center in the view plane, following the mouse drag
        from 'lastPosition' to 'currentPosition' (both in pixels). The scene follows the cursor:
        whatever lies in the view center plane stays under it for the whole drag.
        """
        offset, distance = self.orbitOffset()
        if offset is None:
            return

        scale = self.worldPerPixel(distance)
        right, up = self.screenAxes((-offset).normalized())
        # Move the camera opposite to the drag, so that the scene moves along with it.
        translation = (right * -(currentPosition.x() - lastPosition.x())
                       + up * (currentPosition.y() - lastPosition.y())) * scale

        self._camera.setPosition(self._camera.position() + translation)
        self._camera.setViewCenter(self._camera.viewCenter() + translation)

    @Slot(float, QPointF)
    def zoom(self, steps, cursorPosition):
        """
        Dolly the camera by 'steps' zoom steps: positive steps move it closer to its view center.
        When 'zoomToCursor' is set, the view center also slides towards the point under
        'cursorPosition' (in pixels), keeping that point still while the view scales around it.
        """
        offset, distance = self.orbitOffset()
        if offset is None or steps == 0.0:
            return

        ratio = max(pow(self.zoomFactor, steps), self.minZoomRatio)
        viewCenter = self._camera.viewCenter()
        if self._zoomToCursor:
            viewCenter = viewCenter + self.cursorOffset(cursorPosition, distance) * (1.0 - ratio)

        self._camera.setViewCenter(viewCenter)
        self._camera.setPosition(viewCenter + offset * ratio)

    @Slot(QPointF, QPointF, QPointF)
    def zoomByDrag(self, anchorPosition, lastPosition, currentPosition):
        """
        Zoom by a horizontal drag from 'lastPosition' to 'currentPosition' (dragging right zooms in),
        towards the point under 'anchorPosition', where the drag started (all in pixels).
        """
        if self._windowSize.isEmpty():
            return
        dx = (currentPosition.x() - lastPosition.x()) / self._windowSize.height()
        self.zoom(dx * self.dragZoomSteps, anchorPosition)

    def cursorOffset(self, cursorPosition, distance):
        """ World offset, in the view center plane, from the view center to the point under the cursor. """
        offset, _ = self.orbitOffset()
        if offset is None:
            return QVector3D()
        scale = self.worldPerPixel(distance)
        right, up = self.screenAxes((-offset).normalized())
        # Viewport y points down, world up points the other way.
        return (right * (cursorPosition.x() - self._windowSize.width() * 0.5)
                - up * (cursorPosition.y() - self._windowSize.height() * 0.5)) * scale

    windowSizeChanged = Signal()
    windowSize = makeProperty(QSize, '_windowSize', windowSizeChanged)
    cameraChanged = Signal()
    camera = makeProperty(QObject, '_camera', cameraChanged)
    rotationSpeedChanged = Signal()
    rotationSpeed = makeProperty(float, '_rotationSpeed', rotationSpeedChanged)
    zoomToCursorChanged = Signal()
    zoomToCursor = makeProperty(bool, '_zoomToCursor', zoomToCursorChanged)


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

        # Get initial rotation
        qStart = QQuaternion.fromEulerAngles(euler.y(), euler.x(), euler.z())

        # Convert input to points on unit sphere
        vStart = self.fromEquirectangular(QVector3D(ptStart))
        vStartdY = self.fromEquirectangular(QVector3D(ptStart.x(), ptStart.y() + delta, 0))
        vEnd = self.fromEquirectangular(QVector3D(ptEnd))

        qAdd = QQuaternion.rotationTo(vStart, vEnd)

        # Get the 3D point on unit sphere which would correspond to the no rotation +X
        vCurrent = qAdd.rotatedVector(vStartdY)
        vIdeal = self.fromEquirectangular(QVector3D(ptEnd.x(), ptEnd.y() + delta, 0))

        # Project on rotation plane
        lambdaEnd = 1 / QVector3D.dotProduct(vEnd, vCurrent)
        lambdaIdeal = 1 / QVector3D.dotProduct(vEnd, vIdeal)
        vPlaneCurrent = lambdaEnd * vCurrent
        vPlaneIdeal = lambdaIdeal * vIdeal

        # Get the directions
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

        # Get initial rotation
        qStart = QQuaternion.fromEulerAngles(euler.y(), euler.x(), euler.z())

        # Convert input to points on unit sphere
        vStart = self.fromEquirectangular(QVector3D(ptStart))
        vEnd = self.fromEquirectangular(QVector3D(ptEnd))

        # Get the 3D point on unit sphere which would correspond to the no rotation +X
        vIdeal = self.fromEquirectangular(QVector3D(ptStart.x(), ptStart.y() + delta, 0))

        # Project on rotation plane
        lambdaEnd = 1 / QVector3D.dotProduct(vStart, vEnd)
        lambdaIdeal = 1 / QVector3D.dotProduct(vStart, vIdeal)
        vPlaneEnd = lambdaEnd * vEnd
        vPlaneIdeal = lambdaIdeal * vIdeal

        # Get the directions
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
        """
        Compute the Screen point corresponding to a World Point.
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
        """
        Translate the QTransform in its local space relatively to an initial state.
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
        """
        Rotate the QTransform in its local space relatively to an initial state.
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
        newRotQuat = initialRotQuat * transformQuat  # Order is important
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
            # QVector3D does not implement [] operator or easy way to access value by index so
            # this little hack is required
            currentRow = list(scaleMat.row(i).toTuple())
            value = currentRow[i] + scaleVecTuple[i]
            # Make sure to have only positive scale (because negative scale can make issues with matrix decomposition)
            value = value if value >= 0 else -value
            currentRow[i] = value

            # Apply the new row to the scale matrix
            scaleMat.setRow(i, QVector4D(currentRow[0], currentRow[1], currentRow[2], currentRow[3]))

        # Compute the new model matrix (POSITION * ROTATION * SCALE) and set it to the Transform
        mat = initialPosMat * initialRotMat * scaleMat
        transformQtInstance.setMatrix(mat)

    @Slot(QMatrix4x4, result="QVariant")
    def modelMatrixToMatrices(self, modelMat):
        """
        Decompose a model matrix into individual matrices.
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
        """
        Compute a model matrix from three Vector3D.
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
        """
        Convert rotation (euler angles) from Computer Vision to Computer Graphics coordinate system (like OpenGL).
        """
        M = QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), 180.0)

        quaternion = QQuaternion.fromEulerAngles(rotation)

        U = M * quaternion * M

        return U.toEulerAngles()

    @Slot(QVector3D, QVector3D, float, float, result=QVector3D)
    def getRotatedCameraViewVector(self, camereViewVector, cameraUpVector, pitch, yaw):
        """
        Compute the rotated camera view vector with given pitch and yaw (in degrees).
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
        """
        Compute the length of the screen projected vector axis unit transformed by the model matrix.
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

        worldCenterPoint = unitScaleModelMat.map(QVector4D(0, 0, 0, 1))
        worldAxisUnitPoint = unitScaleModelMat.map(QVector4D(axis.x(), axis.y(), axis.z(), 1))
        screenCenter2D = self.pointFromWorldToScreen(worldCenterPoint, camera, windowSize)
        screenAxisUnitPoint2D = self.pointFromWorldToScreen(worldAxisUnitPoint, camera, windowSize)

        screenVector = QVector2D(screenAxisUnitPoint2D.x() - screenCenter2D.x(),
                                 -(screenAxisUnitPoint2D.y() - screenCenter2D.y()))

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
        """
        Decompose a model matrix into individual component.
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
