#include "GLView.hpp"
#include "GLRenderer.hpp"
#include "models/CameraModel.hpp"
#include <QtQuick/QQuickWindow>
#include <QtMath>
#include <iostream>

namespace mockup
{

GLView::GLView()
    : _renderer(nullptr)
    , _cameraMode(Idle)
    , _lookAtTmp() // Stores camera->_lookAtTmp locally to avoid recomputing it
{
    // FIXME: camera location should move away
    QUrl fakeurl;
    setCamera(new CameraModel(fakeurl, nullptr));

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

const QColor& GLView::color() const
{
    return _color;
}

void GLView::setColor(const QColor& color)
{
    if(color == _color)
        return;
    _color = color;
    emit colorChanged();
    refresh();
}

QObject* GLView::camera() const
{
    return _camera;
}

// NOTE : is this the same as setCurrentCamera
void GLView::setCamera(QObject* camera)
{
    if(camera == _camera)
        return;

    _camera = dynamic_cast<CameraModel*>(camera);
    if(_camera)
    {
        // FIXME: do we need to disconnect the previous camera if any ?
        connect(_camera, SIGNAL(viewMatrixChanged()), this, SLOT(refresh()), Qt::DirectConnection);
        _lookAtTmp = _camera->lookAt();
        emit cameraChanged();
        refresh();
    }
}

void GLView::handleWindowChanged(QQuickWindow* win)
{
    if(!win)
        return;
    connect(win, SIGNAL(beforeRendering()), this, SLOT(paint()), Qt::DirectConnection);
    connect(win, SIGNAL(beforeSynchronizing()), this, SLOT(sync()), Qt::DirectConnection);
    win->setClearBeforeRendering(false);
}

// This function is called from XXXXX
// when the GL context is current
void GLView::sync()
{
    // First time
    if(!_renderer)
        _renderer = new GLRenderer();

    qreal ratio = window()->devicePixelRatio();

    QPointF pos(x(), y());
    pos = mapToScene(pos);
    _viewport.setX(qRound(ratio * pos.x()));
    _viewport.setY(qRound(ratio * (window()->height() - (pos.y() + height()))));
    _viewport.setWidth(qRound(ratio * width()));
    _viewport.setHeight(qRound(ratio * height()));

    _renderer->setViewportSize(_viewport.size());
    _renderer->setClearColor(_color);

    // camera
    if(_camera)
        _renderer->setCameraMatrix(_camera->viewMatrix());

    // Triggers a load when the file name is not null
    if(!_alembicSceneFile.isEmpty())
    {
        _renderer->addAlembicScene(_alembicSceneFile);
        _alembicSceneFile.clear();
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

void GLView::addAlembicScene(const QString& filename)
{
    // Stores the filename, the load is done later on
    // in the sync function, inside a GL context
    _alembicSceneFile = filename;
    refresh();
}

void GLView::mousePressEvent(QMouseEvent* event)
{
    // Dependending on the combination of key and mouse
    // set the correct mode
    if(!_camera)
        return;
    if(event->modifiers() == Qt::AltModifier)
    {
        _mousePos = event->pos();
        _camMatTmp = _camera->viewMatrix();
        _lookAtTmp = _camera->lookAt();
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

    QQuaternion ry(1, y * dx * 0.01);
    QQuaternion rx(1, -x * dy * 0.01);
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

    QQuaternion ry(1, -y * dx * 0.01);
    ry.normalize();
    QQuaternion rx(1, -x * dy * 0.01);
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
    if(!_camera)
        return;

    const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
    const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
    const int numDegrees = event->delta() / 8;
    const int numSteps = numDegrees / 15;
    const float delta = numSteps * 100;

    float radius = _camera->lookAtRadius();
    translateLineOfSightCamera(_camMatTmp, radius, delta, 0);

    _camera->setLookAtRadius(radius);
    _camera->setViewMatrix(_camMatTmp);

    _lookAtTmp = _camera->lookAt();
    _mousePos = event->pos();
}

void GLView::mouseMoveEvent(QMouseEvent* event)
{
    if(!_camera)
        return;

    switch(_cameraMode)
    {
        case Idle:
            break;
        case Rotate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?
            if(0) // TODO select between trackball vs turntable
            {
                trackBallRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);

                _camera->setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
            else // Turntable
            {
                turnTableRotateCamera(_camMatTmp, _lookAtTmp, dx, dy);

                _camera->setViewMatrix(_camMatTmp);
                _mousePos = event->pos();
            }
        }
        break;
        case Translate:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?

            planeTranslateCamera(_camMatTmp, dx, dy);

            _camera->setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera->lookAt();
            _mousePos = event->pos();
        }
        break;
        case Zoom:
        {
            const float dx = _mousePos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _mousePos.y() - event->pos().y(); // or unproject ?

            float radius = _camera->lookAtRadius();
            translateLineOfSightCamera(_camMatTmp, radius, dx, dy);

            _camera->setLookAtRadius(radius);
            _camera->setViewMatrix(_camMatTmp);
            _lookAtTmp = _camera->lookAt();
            _mousePos = event->pos();
        }

        break;
        default:
            break;
    }
}

void GLView::mouseReleaseEvent(QMouseEvent* event)
{
    _cameraMode = Idle;
}

} // namespace
