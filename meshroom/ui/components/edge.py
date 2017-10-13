from PySide2.QtCore import Signal, Property, QPointF, Qt, QObject
from PySide2.QtGui import QPainterPath, QVector2D
from PySide2.QtQuick import QQuickItem


class MouseEvent(QObject):
    """
    Simple MouseEvent object, since QQuickMouseEvent is not accessible in the public API
    """
    def __init__(self, evt):
        super(MouseEvent, self).__init__()
        self._x = evt.x()
        self._y = evt.y()
        self._button = evt.button()

    x = Property(float, lambda self: self._x, constant=True)
    y = Property(float, lambda self: self._y, constant=True)
    button = Property(Qt.MouseButton, lambda self: self._button, constant=True)


class EdgeMouseArea(QQuickItem):
    """
    Provides a MouseArea shaped as a cubic spline for mouse interaction with edges.

    Note: for performance reason, shape is updated only when geometry changes since this is the main use-case with edges.
    TODOs:
        - update when start/end points change too
        - review this when using new QML Shape module
    """
    def __init__(self, parent=None):
        super(EdgeMouseArea, self).__init__(parent)

        self._viewScale = 1.0
        self._startX = 0.0
        self._startY = 0.0
        self._endX = 0.0
        self._endY = 0.0
        self._curveScale = 0.7
        self._edgeThickness = 1.0
        self._hullThickness = 2.0
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

    def geometryChanged(self, newGeometry, oldGeometry):
        super(EdgeMouseArea, self).geometryChanged(newGeometry, oldGeometry)
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
        p1 = QPointF(self._startX, self._startY)
        p2 = QPointF(self._endX, self._endY)
        ctrlPt = QPointF(self.ctrlPtDist, 0)
        path = QPainterPath(p1)
        path.cubicTo(p1 + ctrlPt, p2 - ctrlPt, p2)

        # Compute offset on x and y axis
        hullOffset = self._edgeThickness * self._viewScale + self._hullThickness
        v = QVector2D(p2 - p1).normalized()
        offset = QPointF(hullOffset * -v.y(), hullOffset * v.x())

        self._path = QPainterPath(path.toReversed())
        self._path.translate(-offset)
        path.translate(offset)
        self._path.connectPath(path)

    @property
    def thickness(self):
        return self._hullThickness

    @thickness.setter
    def thickness(self, value):
        if self._hullThickness == value:
            return
        self._hullThickness = value
        self.thicknessChanged.emit()

    @property
    def edgeThickness(self):
        return self._edgeThickness

    @edgeThickness.setter
    def edgeThickness(self, value):
        if self._edgeThickness == value:
            return
        self._edgeThickness = value
        self.thicknessChanged.emit()

    @property
    def viewScale(self):
        return self._viewScale

    @viewScale.setter
    def viewScale(self, value):
        if self.viewScale == value:
            return
        self._viewScale = value
        self.viewScaleChanged.emit()

    @property
    def startX(self):
        return self._startX
    
    @startX.setter
    def startX(self, value):
        self._startX = value
        self.startXChanged.emit()

    @property
    def startY(self):
        return self._startY

    @startY.setter
    def startY(self, value):
        self._startY = value
        self.startYChanged.emit()

    @property
    def endX(self):
        return self._endX

    @endX.setter
    def endX(self, value):
        self._endX = value
        self.endXChanged.emit()

    @property
    def endY(self):
        return self._endY

    @endY.setter
    def endY(self, value):
        self._endY = value
        self.endYChanged.emit()

    @property
    def curveScale(self):
        return self._curveScale

    @curveScale.setter
    def curveScale(self, value):
        self._curveScale = value
        self.curveScaleChanged.emit()
        self.updateShape()

    @property
    def ctrlPtDist(self):
        return self.width() * self.curveScale * (-1 if self._startX > self._endX else 1)

    @property
    def containsMouse(self):
        return self._containsMouse

    def setContainsMouse(self, value):
        if self._containsMouse == value:
            return
        self._containsMouse = value
        self.containsMouseChanged.emit()

    thicknessChanged = Signal()
    thickness = Property(float, thickness.fget, thickness.fset, notify=thicknessChanged)
    edgeThicknessChanged = Signal()
    edgeThickness = Property(float, edgeThickness.fget, edgeThickness.fset, notify=edgeThicknessChanged)
    viewScaleChanged = Signal()
    viewScale = Property(float, viewScale.fget, viewScale.fset, notify=viewScaleChanged)
    startXChanged = Signal()
    startX = Property(float, startX.fget, startX.fset, notify=startXChanged)
    startYChanged = Signal()
    startY = Property(float, startY.fget, startY.fset, notify=startYChanged)
    endXChanged = Signal()
    endX = Property(float, endX.fget, endX.fset, notify=endXChanged)
    endYChanged = Signal()
    endY = Property(float, endY.fget, endY.fset, notify=endYChanged)
    curveScaleChanged = Signal()
    curveScale = Property(float, curveScale.fget, curveScale.fset, notify=curveScaleChanged)
    ctrlPtDistChanged = Signal()
    ctrlPtDist = Property(float, ctrlPtDist.fget, notify=ctrlPtDist)
    containsMouseChanged = Signal()
    containsMouse = Property(float, containsMouse.fget, notify=containsMouseChanged)
    acceptedButtons = Property(int,
                               lambda self: super(EdgeMouseArea, self).acceptedMouseButtons,
                               lambda self, value: super(EdgeMouseArea, self).setAcceptedMouseButtons(value))

    pressed = Signal(MouseEvent)
    released = Signal(MouseEvent)
