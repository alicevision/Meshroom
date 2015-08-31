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
    , _lookAt() // Stores camera->_lookAt locally to avoid recomputing it
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
    if (_camera) 
    {
        // FIXME: do we need to disconnect the previous camera if any ?
        connect(_camera, SIGNAL(viewMatrixChanged()), this, SLOT(refresh()), Qt::DirectConnection);
        _lookAt = _camera->lookAt();
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

void GLView::sync()
{
    if(!_renderer)
        _renderer = new GLRenderer();

    qreal ratio = window()->devicePixelRatio();

    QPointF pos(x(), y());
    pos = mapToScene(pos);
    _rect.setX(qRound(ratio * pos.x()));
    _rect.setY(qRound(ratio * (window()->height() - (pos.y() + height()))));
    _rect.setWidth(qRound(ratio * width()));
    _rect.setHeight(qRound(ratio * height()));

    _renderer->setViewportSize(_rect.size());
    _renderer->setClearColor(_color);

    // camera
    if(_camera)
        _renderer->setCameraMatrix(_camera->viewMatrix());

    if(!_pointCloud.isEmpty())
    {
        _renderer->setPointCloud(_pointCloud);
        _pointCloud.clear();
    }
}

void GLView::paint()
{
    glEnable(GL_SCISSOR_TEST);
    glViewport(_rect.x(), _rect.y(), _rect.width(), _rect.height());
    glScissor(_rect.x(), _rect.y(), _rect.width(), _rect.height());

    if(_renderer)
        _renderer->draw();

    glDisable(GL_SCISSOR_TEST);
}

void GLView::refresh()
{
    if(_renderer)
        _renderer->setGizmoPosition(_lookAt);
    if(window())
        window()->update();
}

void GLView::setPointCloud(const QString& cloud)
{
    _pointCloud = cloud;
    refresh();
}

void GLView::mousePressEvent(QMouseEvent* event)
{
    // Dependending on the combination of key and mouse
    // set the correct mode
    if(event->modifiers() == Qt::AltModifier)
    {
        _pressedPos = event->pos();
        _cameraBegin = _camera->viewMatrix();
        _lookAt = _camera->lookAt();
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


void GLView::trackBallRotateCamera(QMatrix4x4 &cam, const QVector3D &lookAt, float dx, float dy)
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

void GLView::turnTableRotateCamera(QMatrix4x4 &cam, const QVector3D &lookAt, float dx, float dy)
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

void GLView::planeTranslateCamera(QMatrix4x4 &cam, float dx, float dy)
{
    QVector3D x(cam.row(0));
    x.normalize();

    QVector3D y(cam.row(1));
    y.normalize();

    cam.translate(-x * 0.01 * dx);
    cam.translate(y * 0.01 * dy);
}

void GLView::translateLineOfSightCamera(QMatrix4x4 &cam, float &radius, float dx, float dy)
{
    QVector3D z(cam.row(2));
    z.normalize();
    const float offset = 0.01 * (dx + dy);
    cam.translate(-z * offset);
    radius += offset;
}

void GLView::wheelEvent(QWheelEvent* event)
{
    const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
    const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?
    const int numDegrees = event->delta() / 8;
    const int numSteps = numDegrees / 15;
    const float delta = numSteps*100;

    float radius = _camera->lookAtRadius();
    translateLineOfSightCamera(_cameraBegin, radius, delta, 0);

    _camera->setLookAtRadius(radius);
    _camera->setViewMatrix(_cameraBegin);

    _lookAt = _camera->lookAt();
    _pressedPos = event->pos();
}

void GLView::mouseMoveEvent(QMouseEvent* event)
{
    switch(_cameraMode)
    {
        case Idle:
            break;
        case Rotate:
        {
            const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?
            if(0) // TODO select between trackball vs turntable
            {
                trackBallRotateCamera(_cameraBegin, _lookAt, dx, dy);

                _camera->setViewMatrix(_cameraBegin);
                _pressedPos = event->pos();
            }
            else // Turntable
            {
                turnTableRotateCamera(_cameraBegin, _lookAt, dx, dy);

                _camera->setViewMatrix(_cameraBegin);
                _pressedPos = event->pos();
            }
        }
        break;
        case Translate:
        {
            const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?

            planeTranslateCamera(_cameraBegin, dx, dy);

            _camera->setViewMatrix(_cameraBegin);
            _lookAt = _camera->lookAt();
            _pressedPos = event->pos();
        }
        break;
        case Zoom:
        {
            const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?

            float radius = _camera->lookAtRadius();
            translateLineOfSightCamera(_cameraBegin, radius, dx, dy);

            _camera->setLookAtRadius(radius);
            _camera->setViewMatrix(_cameraBegin);
            _lookAt = _camera->lookAt();
            _pressedPos = event->pos();
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
