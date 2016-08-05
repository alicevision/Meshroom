#include "GLView.hpp"
#include "GLRenderer.hpp"
#include <QtQuick/QQuickWindow>
#include <QtMath>

namespace meshroom
{

GLView::GLView()
    : _renderer(nullptr)
    , _cameraMode(Idle)
    , _lookAtTmp(_camera.lookAt()) // Stores camera._lookAt locally to avoid recomputing it
    , _camMatTmp(_camera.viewMatrix())
{
    setKeepMouseGrab(true);
    setAcceptedMouseButtons(Qt::AllButtons);
    setFlag(ItemAcceptsInputMethod, true);
    connect(this, SIGNAL(windowChanged(QQuickWindow*)), this,
            SLOT(handleWindowChanged(QQuickWindow*)));
}

GLView::~GLView()
{
    if(_renderer)
        delete _renderer;
}

void GLView::setPointSize(const float& size)
{
    if(size == _pointSize)
        return;
    _pointSize = size;
    Q_EMIT pointSizeChanged();
    _syncPointSize = true;
    refresh();
}

void GLView::setAlembicScene(const QUrl& url)
{
    if(url == _alembicScene)
        return;
    _alembicScene = url;
    Q_EMIT alembicSceneChanged();
    _syncAlembicScene = true;
    refresh();
}

void GLView::setGridVisibility(const bool& visible)
{
    if(visible == _gridVisibility)
        return;
    _gridVisibility = visible;
    Q_EMIT gridVisibilityChanged();
    _syncGridVisibility = true;
    refresh();
}

void GLView::setGizmoVisibility(const bool& visible)
{
    if(visible == _gizmoVisibility)
        return;
    _gizmoVisibility = visible;
    Q_EMIT gizmoVisibilityChanged();
    _syncGizmoVisibility = true;
    refresh();
}

void GLView::setCameraVisibility(const bool& visible)
{
    if(visible == _cameraVisibility)
        return;
    _cameraVisibility = visible;
    Q_EMIT cameraVisibilityChanged();
    _syncCameraVisibility = true;
    refresh();
}

void GLView::setCameraScale(const float& scale)
{
    if(scale == _cameraScale)
        return;
    _cameraScale = scale;
    Q_EMIT cameraScaleChanged();
    _syncCameraScale = true;
    refresh();
}

void GLView::handleWindowChanged(QQuickWindow* win)
{
    if(!win)
        return;
    connect(win, SIGNAL(beforeRendering()), this, SLOT(paint()), Qt::DirectConnection);
    connect(win, SIGNAL(beforeSynchronizing()), this, SLOT(sync()), Qt::DirectConnection);
    win->setClearBeforeRendering(false);
}

void GLView::sync()
{
    if(!_renderer) // first time
        _renderer = new GLRenderer();

    qreal ratio = window()->devicePixelRatio();
    QPointF pos(x(), y());
    pos = mapToScene(pos);
    _viewport.setX(qRound(ratio * pos.x()));
    _viewport.setY(qRound(ratio * (window()->height() - (pos.y() + height()))));
    _viewport.setWidth(qRound(ratio * width()));
    _viewport.setHeight(qRound(ratio * height()));
    _renderer->setViewportSize(_viewport.size());

    if(_syncCameraMatrix)
    {
        _renderer->setCameraMatrix(_camera.viewMatrix());
        _syncCameraMatrix = false;
    }
    if(_syncPointSize)
    {
        _renderer->setPointSize(_pointSize);
        _syncPointSize = false;
    }
    if(_syncAlembicScene)
    {
        _renderer->resetScene();
        _renderer->addAlembicScene(_alembicScene);
        _syncAlembicScene = false;
    }
    if(_syncGridVisibility)
    {
        _renderer->setGridVisibility(_gridVisibility);
        _syncGridVisibility = false;
    }
    if(_syncGizmoVisibility)
    {
        _renderer->setGizmoVisibility(_gizmoVisibility);
        _syncGizmoVisibility = false;
    }
    if(_syncCameraVisibility)
    {
        _renderer->setCameraVisibility(_cameraVisibility);
        _syncCameraVisibility = false;
    }
    if(_syncCameraScale)
    {
        _renderer->setCameraScale(_cameraScale);
        _syncCameraScale = false;
    }
}

void GLView::paint()
{
    glEnable(GL_SCISSOR_TEST);
    glViewport(_viewport.x(), _viewport.y(), _viewport.width(), _viewport.height());
    glScissor(_viewport.x(), _viewport.y(), _viewport.width(), _viewport.height());

    if(_renderer)
        _renderer->draw();

    glDisable(GL_SCISSOR_TEST);
}

void GLView::refresh()
{
    if(window())
        window()->update();
}

void GLView::mousePressEvent(QMouseEvent* event)
{
    // Dependending on the combination of key and mouse
    // set the correct mode
    if(event->modifiers() == Qt::AltModifier)
    {
        _mousePos = event->pos();
        _camMatTmp = _camera.viewMatrix();
        _lookAtTmp = _camera.lookAt();
        switch(event->buttons())
        {
            case Qt::LeftButton:
                _cameraMode = Rotate;
                break;
            case Qt::MidButton:
                _cameraMode = Translate;
                break;
            case Qt::RightButton:
                _cameraMode = Zoom;
                break;
            default:
                break;
        }
    }
    refresh();
}

void GLView::trackBallRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy)
{
    QVector3D x(cam.row(0).x(), cam.row(0).y(), cam.row(0).z());
    x.normalize();

    QVector3D y(cam.row(1).x(), cam.row(1).y(), cam.row(1).z());
    y.normalize();

    QQuaternion ry(1, y * dx * 0.005);
    QQuaternion rx(1, -x * dy * 0.005);
    rx.normalize();
    ry.normalize();
    cam.translate(lookAt);
    cam.rotate(rx * ry);
    cam.translate(-lookAt);
}

void GLView::turnTableRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy)
{
    QVector3D x(cam.row(0));
    x.normalize();

    QVector3D y(0, 1, 0);
    y.normalize();

    const float sign = cam.row(1).y() > 0 ? 1.f : -1.f;

    QQuaternion ry(1, -y * dx * 0.005 * sign);
    ry.normalize();
    QQuaternion rx(1, -x * dy * 0.005);
    rx.normalize();

    cam.translate(lookAt);
    cam.rotate(rx * ry);
    cam.translate(-lookAt);
}

void GLView::planeTranslateCamera(QMatrix4x4& cam, float dx, float dy)
{
    QVector3D x(cam.row(0));
    x.normalize();

    QVector3D y(cam.row(1));
    y.normalize();

    cam.translate(-x * 0.01 * dx);
    cam.translate(y * 0.01 * dy);
}

void GLView::translateLineOfSightCamera(QMatrix4x4& cam, float& radius, float dx, float dy)
{
    QVector3D z(cam.row(2));
    z.normalize();
    const float offset = 0.01 * (dx + dy);
    cam.translate(-z * offset);
    radius += offset;
}

void GLView::wheelEvent(QWheelEvent* event)
{
    const int numDegrees = event->delta() / 8;
    const int numSteps = numDegrees / 15;
    const float delta = numSteps * 100;

    float radius = _camera.lookAtRadius();
    translateLineOfSightCamera(_camMatTmp, radius, -delta, 0);
    _camera.setLookAtRadius(radius);
    _camera.setViewMatrix(_camMatTmp);
    _lookAtTmp = _camera.lookAt();
    _mousePos = event->pos();

    _syncCameraMatrix = true;
    refresh();
}

void GLView::mouseMoveEvent(QMouseEvent* event)
{
    switch(_cameraMode)
    {
        case Idle:
            return;
        case Rotate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            if(0) // TODO select between trackball vs turntable
            {
                trackBallRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);
                _camera.setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
            else // Turntable
            {
                turnTableRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);
                _camera.setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
        }
        break;
        case Translate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            planeTranslateCamera(_camMatTmp, dx, dy);
            _camera.setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera.lookAt();
            _mousePos = event->pos();
        }
        break;
        case Zoom:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            float radius = _camera.lookAtRadius();
            translateLineOfSightCamera(_camMatTmp, radius, dx, dy);
            _camera.setLookAtRadius(radius);
            _camera.setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera.lookAt();
            _mousePos = event->pos();
        }
        break;
        default:
            break;
    }

    _syncCameraMatrix = true;
    refresh();
}

void GLView::mouseReleaseEvent(QMouseEvent* event)
{
    _cameraMode = Idle;
}

} // namespace
