#include "GLView.hpp"
#include "GLRenderer.hpp"
#include "models/CameraModel.hpp"
#include <QtQuick/QQuickWindow>

namespace mockup
{

GLView::GLView()
    : _renderer(nullptr)
{
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

void GLView::setCamera(QObject* camera)
{
    if(camera == _camera)
        return;
    _camera = camera;
    connect(_camera, SIGNAL(eyeChanged()), this, SLOT(refresh()), Qt::DirectConnection);
    connect(_camera, SIGNAL(centerChanged()), this, SLOT(refresh()), Qt::DirectConnection);
    connect(_camera, SIGNAL(upChanged()), this, SLOT(refresh()), Qt::DirectConnection);
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
    _rect = QRect(int(ratio * parentItem()->x()), int(ratio * parentItem()->y()),
                  int(ratio * parentItem()->width()), int(ratio * parentItem()->height()));
    _renderer->setViewportSize(_rect.size());
    _renderer->setClearColor(_color);

    // camera
    CameraModel* cameraModel = dynamic_cast<CameraModel*>(_camera);
    if(cameraModel)
        _renderer->setCameraMatrix(cameraModel->viewMatrix());
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
    if(window())
        window()->update();
}

} // namespace
