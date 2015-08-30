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
    , _lookAt() // Store locally camera->_lookAt to avoid recomputing it
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

    // FIXME: do we need to disconnect the previous camera if any ?

    _camera = camera;
    connect(_camera, SIGNAL(viewMatrixChanged()), this, SLOT(refresh()), Qt::DirectConnection);
    CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
    _lookAt = cameraModel->lookAt();
    emit cameraChanged();
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
    CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
    if(cameraModel)
        _renderer->setCameraMatrix(cameraModel->viewMatrix());

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
        CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
        _cameraBegin = cameraModel->viewMatrix();
        _lookAt = cameraModel->lookAt();
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
                QMatrix4x4 cam(_cameraBegin);
                QVector3D x(cam.row(0).x(), cam.row(0).y(), cam.row(0).z());
                x.normalize();

                QVector3D y(cam.row(1).x(), cam.row(1).y(), cam.row(1).z());
                y.normalize();

                QQuaternion ry(1, y * dx * 0.01);
                QQuaternion rx(1, -x * dy * 0.01);
                rx.normalize();
                ry.normalize();
                cam.translate(_lookAt);
                cam.rotate(rx * ry);
                cam.translate(-_lookAt);
                CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
                cameraModel->setViewMatrix(cam);
                _pressedPos = event->pos();
                _cameraBegin = cam;
            }
            else // Turntable
            {
                QMatrix4x4 cam(_cameraBegin);
                QVector3D x(cam.row(0));
                x.normalize();

                QVector3D y(0, 1, 0);
                y.normalize();

                QQuaternion ry(1, -y * dx * 0.01);
                ry.normalize();
                QQuaternion rx(1, -x * dy * 0.01);
                rx.normalize();

                cam.translate(_lookAt);
                cam.rotate(rx * ry);
                cam.translate(-_lookAt);

                CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
                cameraModel->setViewMatrix(cam);
                _pressedPos = event->pos();
                _cameraBegin = cam;
            }
        }
        break;
        case Translate:
        {
            const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?
            QMatrix4x4 cam(_cameraBegin);

            QVector3D x(cam.row(0));
            x.normalize();

            QVector3D y(cam.row(1));
            y.normalize();

            cam.translate(-x * 0.01 * dx);
            cam.translate(y * 0.01 * dy);

            CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
            cameraModel->setViewMatrix(cam);
            _lookAt = cameraModel->lookAt();
            _pressedPos = event->pos();
            _cameraBegin = cam;
        }
        break;
        case Zoom:
        {
            const float dx = _pressedPos.x() - event->pos().x(); // TODO divide by canvas size
            const float dy = _pressedPos.y() - event->pos().y(); // or unproject ?

            QMatrix4x4 cam(_cameraBegin);

            QVector3D z(cam.row(2));
            z.normalize();
            float offset = 0.01 * (dx + dy);
            cam.translate(-z * offset);
            CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
            cameraModel->setViewMatrix(cam);
            float radius = cameraModel->lookAtRadius();
            radius += offset;
            if(radius > 0.0)
                cameraModel->setLookAtRadius(radius);
            else
                cameraModel->setLookAtRadius(0.0);
            _lookAt = cameraModel->lookAt();
            _pressedPos = event->pos();
            _cameraBegin = cam;
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
