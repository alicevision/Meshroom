#pragma once

#include <QtQuick/QQuickItem>
#include <QMatrix4x4>
#include "models/Camera.hpp"

namespace meshroom
{

// forward declarations
class GLRenderer;

class GLView : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY colorChanged)

public:
    GLView();
    ~GLView();

public:
    Q_SLOT const QColor& color() const { return _color; }
    Q_SLOT void setColor(const QColor& color);
    Q_SLOT void loadAlembicScene(const QUrl& url);
    Q_SIGNAL void colorChanged();

private:
    Q_SLOT void handleWindowChanged(QQuickWindow* win);
    Q_SLOT void sync();
    Q_SLOT void paint();
    Q_SLOT void refresh();

protected:
    void mouseMoveEvent(QMouseEvent*);
    void mousePressEvent(QMouseEvent*);
    void mouseReleaseEvent(QMouseEvent*);
    void wheelEvent(QWheelEvent* event);

protected:
    // Function to manipulate cameras.
    // might move in a different class, eg CameraManipulator
    void trackBallRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy);
    void turnTableRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy);
    void planeTranslateCamera(QMatrix4x4& cam, float dx, float dy);
    void translateLineOfSightCamera(QMatrix4x4& cam, float& radius, float dx, float dy);

private:
    GLRenderer* _renderer = nullptr;
    QRect _viewport;
    QColor _color;
    Camera _camera;
    QUrl _alembicSceneUrl;
    // Ideally the following variables should go in a manipulator of some sort
    QPoint _mousePos;      // Position of the mousePressed event
    QMatrix4x4 _camMatTmp; // Position of the camera when the mouse is pressed
    QVector3D _lookAtTmp;
    enum CameraMode
    {
        Idle,
        Rotate,
        Translate,
        Zoom
    } _cameraMode;
};

} // namespace
