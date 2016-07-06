#pragma once

#include <QtQuick/QQuickItem>
#include <QMatrix4x4>
#include "models/Camera.hpp"
#include <iostream>

namespace meshroom
{

// forward declarations
class GLRenderer;

class GLView : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY colorChanged)
    Q_PROPERTY(bool showCameras READ showCameras WRITE setShowCameras NOTIFY showCamerasChanged)

public:
    GLView();
    ~GLView();

    bool showCameras() const;
    void setShowCameras(bool v);

public slots:
    const QColor& color() const { return _color; }
    void setColor(const QColor& color);
    void loadAlembicScene(const QUrl& url);

private slots:
    void handleWindowChanged(QQuickWindow* win);
    void sync();
    void paint();
    void refresh();

signals:
    void colorChanged();
    void showCamerasChanged();

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
    // Delegate opengl rendering
    GLRenderer* _renderer = nullptr;
    QRect _viewport;
    QColor _color;
    Camera _camera;
    QUrl _alembicSceneUrl;
    // FIXME : rename variables to something more meaningful
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
    bool _showCameras;
};

} // namespace
