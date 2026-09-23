from math import acos, asin, degrees

import pytest

from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QVector3D

try:
    from PySide6.Qt3DRender import Qt3DRender
    from meshroom.ui.components.scene3D import TurntableCameraController
except ImportError:  # Qt3D is an optional PySide6 add-on
    Qt3DRender = None

pytestmark = pytest.mark.skipif(Qt3DRender is None, reason="Qt3D is required by the 3D viewer helpers")


WINDOW = QSize(800, 600)
UP = QVector3D(0.0, 1.0, 0.0)


def makeController(position=QVector3D(12.0, 10.0, -12.0), viewCenter=QVector3D(0.0, 0.0, 0.0), windowSize=WINDOW):
    camera = Qt3DRender.QCamera()
    camera.setProjectionType(Qt3DRender.QCameraLens.PerspectiveProjection)
    camera.setFieldOfView(45.0)
    camera.setAspectRatio(windowSize.width() / windowSize.height())
    camera.setPosition(position)
    camera.setViewCenter(viewCenter)
    camera.setUpVector(UP)

    controller = TurntableCameraController()
    controller.windowSize = windowSize
    controller.camera = camera
    return controller


def drag(controller, dx, dy, steps=10, manipulate=None, origin=(400.0, 300.0)):
    """
    Simulate a mouse drag of (dx, dy) pixels starting from 'origin', split in incremental
    moves as the MouseHandler does, and return the position the cursor ends up at.
    'manipulate' defaults to orbiting; pass 'controller.pan' to drag the view instead.
    """
    x, y = origin
    for _ in range(steps):
        (manipulate or controller.rotate)(QPointF(x, y), QPointF(x + dx / steps, y + dy / steps))
        x += dx / steps
        y += dy / steps
    return x, y


def project(camera, point, windowSize=WINDOW):
    """ Viewport position, in pixels, at which the given world point is drawn. """
    clip = (camera.projectionMatrix() * camera.viewMatrix()).map(point)
    return ((clip.x() * 0.5 + 0.5) * windowSize.width(), (0.5 - clip.y() * 0.5) * windowSize.height())


def distance(camera):
    return (camera.position() - camera.viewCenter()).length()


def copy(vector):
    """ Snapshot of a vector, to compare against after the camera has moved. """
    return QVector3D(vector.x(), vector.y(), vector.z())


def elevation(camera):
    """ Angle, in degrees, between the ground plane and the camera position seen from the view center. """
    direction = (camera.position() - camera.viewCenter()).normalized()
    return degrees(asin(QVector3D.dotProduct(direction, UP)))


def roll(camera):
    """ Angle, in degrees, between the camera up vector and a perfectly levelled one (0 means no roll). """
    viewDirection = (camera.viewCenter() - camera.position()).normalized()
    levelled = (UP - viewDirection * QVector3D.dotProduct(UP, viewDirection)).normalized()
    cosine = QVector3D.dotProduct(levelled, camera.upVector().normalized())
    return degrees(acos(max(-1.0, min(cosine, 1.0))))


def test_horizontalDragOnlyYaws():
    """ A horizontal drag orbits around the up axis: elevation, distance and levelling are preserved. """
    controller = makeController()
    camera = controller.camera
    distance = (camera.position() - camera.viewCenter()).length()

    drag(controller, 200, 0)

    assert elevation(camera) == pytest.approx(30.5088, abs=1e-3)
    assert (camera.position() - camera.viewCenter()).length() == pytest.approx(distance, abs=1e-4)
    assert roll(camera) == pytest.approx(0.0, abs=1e-5)


def test_dragOverViewportHeightRotatesByRotationSpeed():
    """ Dragging over the whole viewport height yaws the camera by 'rotationSpeed' degrees. """
    controller = makeController(position=QVector3D(0.0, 0.0, 10.0))
    controller.rotationSpeed = 180.0

    drag(controller, WINDOW.height(), 0, steps=100)

    # Half a turn around the up axis: the camera ends up on the opposite side of the view center.
    assert controller.camera.position().z() == pytest.approx(-10.0, abs=1e-3)
    assert controller.camera.position().x() == pytest.approx(0.0, abs=1e-3)


def test_rotationIsIsotropic():
    """ The same pixel drag yaws and pitches by the same angle, whatever the viewport aspect ratio. """
    for size in (QSize(1600, 400), QSize(800, 800), QSize(600, 1200)):
        controller = makeController(position=QVector3D(0.0, 0.0, 10.0), windowSize=size)
        drag(controller, 100, 0, steps=1)
        yaw = degrees(asin(abs(controller.camera.position().x()) / 10.0))

        controller = makeController(position=QVector3D(0.0, 0.0, 10.0), windowSize=size)
        drag(controller, 0, 100, steps=1)
        pitch = elevation(controller.camera)

        assert yaw == pytest.approx(pitch, abs=1e-3)
        assert yaw == pytest.approx(100.0 / size.height() * controller.rotationSpeed, abs=1e-3)


def test_verticalDragNeverTiltsNorCrossesThePoles():
    """ Whatever the vertical drag, the camera stays levelled and below the elevation limit. """
    for dy in (60, -60, 10 * WINDOW.height(), -10 * WINDOW.height()):
        controller = makeController()
        camera = controller.camera

        drag(controller, 0, dy, steps=100)

        # Near the poles, reading back the elevation from the (single precision) camera position
        # is ill-conditioned, hence the tolerance; the clamping pulls it back on the next move.
        assert abs(elevation(camera)) <= TurntableCameraController.maxElevation + 0.05
        assert roll(camera) == pytest.approx(0.0, abs=1e-3)


def test_dragDirections():
    """ Dragging right orbits the camera to its left, dragging down raises it above the view center. """
    controller = makeController(position=QVector3D(0.0, 0.0, 10.0))
    drag(controller, 50, 0)
    assert controller.camera.position().x() < 0.0

    controller = makeController(position=QVector3D(0.0, 0.0, 10.0))
    drag(controller, 0, 50)
    assert elevation(controller.camera) > 0.0


def test_panKeepsTheGrabbedPointUnderTheCursor():
    """ Whatever lies in the view center plane when the drag starts stays under the cursor. """
    controller = makeController()
    camera = controller.camera
    grabbed = copy(camera.viewCenter())
    startX, startY = project(camera, grabbed)

    endX, endY = drag(controller, 150, 100, steps=50, manipulate=controller.pan, origin=(startX, startY))

    assert project(camera, grabbed) == pytest.approx((endX, endY), abs=1e-2)


def test_panMovesTheViewCenterAlongWithTheCamera():
    """ Panning slides the whole orbit, so the pivot follows and the distance is preserved. """
    controller = makeController()
    camera = controller.camera
    initialPosition = copy(camera.position())
    initialViewCenter = copy(camera.viewCenter())

    drag(controller, 150, 100, steps=50, manipulate=controller.pan)

    translation = camera.position() - initialPosition
    assert (camera.viewCenter() - initialViewCenter).distanceToPoint(translation) == pytest.approx(0.0, abs=1e-4)
    assert translation.length() > 0.0


def test_zoomIsExactlyReversible():
    """ Being multiplicative, zooming in then back out by as many steps restores the distance. """
    controller = makeController()
    initial = distance(controller.camera)

    for _ in range(10):
        controller.zoom(1.0, QPointF(650.0, 150.0))
    assert distance(controller.camera) < initial
    for _ in range(10):
        controller.zoom(-1.0, QPointF(650.0, 150.0))

    assert distance(controller.camera) == pytest.approx(initial, rel=1e-5)


def test_zoomTowardsCursorKeepsThePointUnderItStill():
    """ With 'zoomToCursor' set, the view scales around the point under the cursor. """
    controller = makeController()
    camera = controller.camera
    cursor = QPointF(650.0, 150.0)
    target = camera.viewCenter() + controller.cursorOffset(cursor, distance(camera))
    assert project(camera, target) == pytest.approx((cursor.x(), cursor.y()), abs=1e-2)

    for _ in range(6):
        controller.zoom(1.0, cursor)

    assert project(camera, target) == pytest.approx((cursor.x(), cursor.y()), abs=1e-2)
    assert distance(camera) < 0.3 * 19.7


def test_zoomWithoutCursorTargetIsAPureDolly():
    """ A centered zoom, or a zoom with 'zoomToCursor' cleared, leaves the view center untouched. """
    for cursor, zoomToCursor in ((QPointF(WINDOW.width() / 2, WINDOW.height() / 2), True),
                                 (QPointF(650.0, 150.0), False)):
        controller = makeController()
        controller.zoomToCursor = zoomToCursor
        initial = distance(controller.camera)

        controller.zoom(3.0, cursor)

        assert controller.camera.viewCenter() == QVector3D(0.0, 0.0, 0.0)
        assert distance(controller.camera) == pytest.approx(initial * TurntableCameraController.zoomFactor ** 3, rel=1e-5)


def test_zoomNeverCollapsesTheDistanceInOneStep():
    """ A single huge zoom keeps at least 'minZoomRatio' of the distance to the view center. """
    controller = makeController()
    initial = distance(controller.camera)

    controller.zoom(100.0, QPointF(WINDOW.width() / 2, WINDOW.height() / 2))

    assert distance(controller.camera) == pytest.approx(initial * TurntableCameraController.minZoomRatio, rel=1e-4)


def test_zoomByDragIsIsotropicAndZoomsInToTheRight():
    """ Dragging right zooms in, by an amount that only depends on the viewport height. """
    for size in (QSize(1600, 400), QSize(800, 800)):
        controller = makeController(windowSize=size)
        anchor = QPointF(size.width() / 2, size.height() / 2)
        initial = distance(controller.camera)

        controller.zoomByDrag(anchor, QPointF(0.0, 0.0), QPointF(size.height() / 2.0, 0.0))

        expected = initial * TurntableCameraController.zoomFactor ** (TurntableCameraController.dragZoomSteps / 2)
        assert distance(controller.camera) == pytest.approx(expected, rel=1e-4)


def test_manipulationsAreSafeWithoutValidInput():
    """ Rotating, panning or zooming without camera, window size or distance to the view center is a no-op. """
    for manipulate in ("rotate", "pan"):
        controller = TurntableCameraController()
        controller.windowSize = WINDOW
        drag(controller, 10, 10, manipulate=getattr(controller, manipulate))  # No camera

        controller = makeController()
        controller.windowSize = QSize()
        drag(controller, 10, 10, manipulate=getattr(controller, manipulate))  # No window size

        # Camera position on the view center
        controller = makeController(position=QVector3D(0.0, 0.0, 0.0))
        drag(controller, 10, 10, manipulate=getattr(controller, manipulate))
        assert controller.camera.position() == QVector3D(0.0, 0.0, 0.0)

    controller = TurntableCameraController()
    controller.zoom(1.0, QPointF(0.0, 0.0))  # No camera
    controller.zoomByDrag(QPointF(0.0, 0.0), QPointF(0.0, 0.0), QPointF(10.0, 0.0))  # No window size

    controller = makeController()
    controller.zoom(0.0, QPointF(0.0, 0.0))  # No zoom step
    assert distance(controller.camera) == pytest.approx(19.697716, abs=1e-4)
