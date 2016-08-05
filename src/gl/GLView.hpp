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
    Q_PROPERTY(float pointSize READ pointSize WRITE setPointSize NOTIFY pointSizeChanged)
    Q_PROPERTY(QUrl alembicScene READ alembicScene WRITE setAlembicScene NOTIFY alembicSceneChanged)
    Q_PROPERTY(bool gridVisibility READ gridVisibility WRITE setGridVisibility NOTIFY
                   gridVisibilityChanged)
    Q_PROPERTY(bool gizmoVisibility READ gizmoVisibility WRITE setGizmoVisibility NOTIFY
                   gizmoVisibilityChanged)
    Q_PROPERTY(bool cameraVisibility READ cameraVisibility WRITE setCameraVisibility NOTIFY
                   cameraVisibilityChanged)
    Q_PROPERTY(float cameraScale READ cameraScale WRITE setCameraScale NOTIFY cameraScaleChanged)

    enum CameraMode
    {
        Idle,
        Rotate,
        Translate,
        Zoom
    };

public:
    GLView();
    ~GLView();

public:
    Q_SLOT const float& pointSize() const { return _pointSize; }
    Q_SLOT const QUrl& alembicScene() const { return _alembicScene; }
    Q_SLOT const bool& gridVisibility() const { return _gridVisibility; }
    Q_SLOT const bool& gizmoVisibility() const { return _gizmoVisibility; }
    Q_SLOT const bool& cameraVisibility() const { return _cameraVisibility; }
    Q_SLOT const float& cameraScale() const { return _cameraScale; }
    Q_SLOT void setPointSize(const float& size);
    Q_SLOT void setAlembicScene(const QUrl& url);
    Q_SLOT void setGridVisibility(const bool& visible);
    Q_SLOT void setGizmoVisibility(const bool& visible);
    Q_SLOT void setCameraVisibility(const bool& visible);
    Q_SLOT void setCameraScale(const float& scale);

public:
    Q_SIGNAL void pointSizeChanged();
    Q_SIGNAL void alembicSceneChanged();
    Q_SIGNAL void gridVisibilityChanged();
    Q_SIGNAL void gizmoVisibilityChanged();
    Q_SIGNAL void cameraVisibilityChanged();
    Q_SIGNAL void cameraScaleChanged();

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

    // dynamic properties
    Camera _camera;
    float _pointSize = 1.f;
    QUrl _alembicScene;
    bool _gridVisibility = true;
    bool _gizmoVisibility = true;
    bool _cameraVisibility = true;
    float _cameraScale = 1.f;
    bool _syncCameraMatrix = true;
    bool _syncPointSize = true;
    bool _syncAlembicScene = false;
    bool _syncGridVisibility = true;
    bool _syncGizmoVisibility = true;
    bool _syncCameraVisibility = true;
    bool _syncCameraScale = true;

    // mouse stuff
    // Ideally the following variables should go in a manipulator of some sort
    QPoint _mousePos;      // Position of the mousePressed event
    QMatrix4x4 _camMatTmp; // Position of the camera when the mouse is pressed
    QVector3D _lookAtTmp;
    CameraMode _cameraMode;
};

} // namespace
