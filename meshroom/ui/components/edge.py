from PySide6.QtCore import Signal, Property, QPointF, Qt, QObject
from PySide6.QtGui import QPainterPath, QVector2D
from PySide6.QtQuick import QQuickItem


class MouseEvent(QObject):
    """
    Simple MouseEvent object, since QQuickMouseEvent is not accessible in the public API
    """
    def __init__(self, evt):
        super(MouseEvent, self).__init__()
        self._x = evt.position().x()
        self._y = evt.position().y()
        self._button = evt.button()
        self._modifiers = evt.modifiers()

    x = Property(float, lambda self: self._x, constant=True)
    y = Property(float, lambda self: self._y, constant=True)
    button = Property(Qt.MouseButton, lambda self: self._button, constant=True)
    modifiers = Property(Qt.KeyboardModifier, lambda self: self._modifiers, constant=True)


class EdgeMouseArea(QQuickItem):
    """
    Provides a MouseArea shaped as a cubic spline for mouse interaction with edges.
    Spline goes from (0,0) to (width, height). Works with negative values.
    """
    def __init__(self, parent=None):
        super(EdgeMouseArea, self).__init__(parent)

        self._curveScale = 0.7
        self._thickness = 2.0
        self._containsMouse = False
        self._path = None  # type: QPainterPath

        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.AllButtons)

    def contains(self, point):
        return self._path.contains(point)

    def hoverEnterEvent(self, evt):
        self.setContainsMouse(True)
        super(EdgeMouseArea, self).hoverEnterEvent(evt)

    def hoverLeaveEvent(self, evt):
        self.setContainsMouse(False)
        super(EdgeMouseArea, self).hoverLeaveEvent(evt)

    def geometryChange(self, newGeometry, oldGeometry):
        super(EdgeMouseArea, self).geometryChange(newGeometry, oldGeometry)
        self.updateShape()

    def mousePressEvent(self, evt):
        if not self.acceptedMouseButtons() & evt.button():
            evt.setAccepted(False)
            return
        e = MouseEvent(evt)
        self.pressed.emit(e)
        e.deleteLater()

    def mouseReleaseEvent(self, evt):
        e = MouseEvent(evt)
        self.released.emit(e)
        e.deleteLater()

    def updateShape(self):
        p1 = QPointF(0, 0)
        p2 = QPointF(self.width(), self.height())
        ctrlPt = QPointF(abs(self.width() * self.curveScale), 0)
        path = QPainterPath(p1)
        path.cubicTo(p1 + ctrlPt, p2 - ctrlPt, p2)

        # Compute offset on x and y axis
        halfThickness = self._thickness / 2.0
        v = QVector2D(p2 - p1).normalized()
        offset = QPointF(halfThickness * -v.y(), halfThickness * v.x())

        self._path = QPainterPath(path.toReversed())
        self._path.translate(-offset)
        path.translate(offset)
        self._path.connectPath(path)

    def getThickness(self):
        return self._thickness

    def setThickness(self, value):
        if self._thickness == value:
            return
        self._thickness = value
        self.thicknessChanged.emit()
        self.updateShape()

    def getCurveScale(self):
        return self._curveScale

    def setCurveScale(self, value):
        if self.curveScale == value:
            return
        self._curveScale = value
        self.curveScaleChanged.emit()
        self.updateShape()

    def getContainsMouse(self):
        return self._containsMouse

    def setContainsMouse(self, value):
        if self._containsMouse == value:
            return
        self._containsMouse = value
        self.containsMouseChanged.emit()

    thicknessChanged = Signal()
    thickness = Property(float, getThickness, setThickness, notify=thicknessChanged)
    curveScaleChanged = Signal()
    curveScale = Property(float, getCurveScale, setCurveScale, notify=curveScaleChanged)
    containsMouseChanged = Signal()
    containsMouse = Property(float, getContainsMouse, notify=containsMouseChanged)
    acceptedButtons = Property(int,
                               lambda self: super(EdgeMouseArea, self).acceptedMouseButtons,
                               lambda self, value: super(EdgeMouseArea, self).setAcceptedMouseButtons(Qt.MouseButtons(value)))

    pressed = Signal(MouseEvent)
    released = Signal(MouseEvent)
