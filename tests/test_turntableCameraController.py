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
    camera.setPosition(position)
    camera.setViewCenter(viewCenter)
    camera.setUpVector(UP)

    controller = TurntableCameraController()
    controller.windowSize = windowSize
    controller.camera = camera
    return controller


def drag(controller, dx, dy, steps=10):
    """ Simulate a mouse drag of (dx, dy) pixels, split in incremental moves as the MouseHandler does. """
    x, y = 400.0, 300.0
    for _ in range(steps):
        controller.rotate(QPointF(x, y), QPointF(x + dx / steps, y + dy / steps))
        x += dx / steps
        y += dy / steps


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


def test_rotateIsSafeWithoutValidInput():
    """ Rotating without camera, window size or any distance to the view center must be a no-op. """
    controller = TurntableCameraController()
    controller.windowSize = WINDOW
    drag(controller, 10, 10)  # No camera

    controller = makeController()
    controller.windowSize = QSize()
    drag(controller, 10, 10)  # No window size

    # Camera position on the view center
    controller = makeController(position=QVector3D(0.0, 0.0, 0.0))
    drag(controller, 10, 10)
    assert controller.camera.position() == QVector3D(0.0, 0.0, 0.0)
