#pragma once

#include <QQuickPaintedItem>
#include <QMatrix4x4>
#include "models/Camera.hpp"
#include <iostream>

namespace meshroom
{

// forward declarations
class GLRenderer;

class GLView : public QQuickPaintedItem
{
    Q_OBJECT
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY colorChanged)
    Q_PROPERTY(bool showCameras READ showCameras WRITE setShowCameras NOTIFY showCamerasChanged)
    Q_PROPERTY(bool showGrid READ showGrid WRITE setShowGrid NOTIFY showGridChanged)

public:
    GLView();
    ~GLView();

    bool showCameras() const;
    void setShowCameras(bool v);
    bool showGrid() const;
    void setShowGrid(bool v);
    void paint(QPainter*) override;

public slots:
    const QColor& color() const { return _color; }
    void setColor(const QColor& color);
    void loadAlembicScene(const QUrl& url);
    void definePlane();
    void clearPlane();

private slots:
    void handleWindowChanged(QQuickWindow* win);
    void sync();
    void drawgl();
    void refresh();

signals:
    void openPopup();
    void colorChanged();
    void showCamerasChanged();
    void showGridChanged();

protected:
    void mousePressEvent(QMouseEvent*) override;
    void mouseMoveEvent(QMouseEvent*) override;
    void mouseReleaseEvent(QMouseEvent*) override;
    void wheelEvent(QWheelEvent* event) override;


private:
    // Function to manipulate cameras. Might move in a different class, eg CameraManipulator
    void handleCameraMousePressEvent(QMouseEvent*);
    void handleCameraMouseMoveEvent(QMouseEvent*);
    void trackBallRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy);
    void turnTableRotateCamera(QMatrix4x4& cam, const QVector3D& lookAt, float dx, float dy);
    void planeTranslateCamera(QMatrix4x4& cam, float dx, float dy);
    void translateLineOfSightCamera(QMatrix4x4& cam, float& radius, float dx, float dy);
    
    // Functions to manipulate the selection.
    void handleSelectionMousePressEvent(QMouseEvent*);
    void handleSelectionMouseReleaseEvent(QMouseEvent*);
    void handleSelectionMouseMoveEvent(QMouseEvent*);
    

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
    
    // Point selection handling.
    QRect _selectedAreaTmp;
    QRect _selectedArea;
    bool _clearSelection = false;
    
    const std::vector<QVector3D>* _selectedPoints;  // owned by the renderer!
    QVector3D _planeNormal;
    QVector3D _planeOrigin;
    bool _planeDefined = false;
    bool _clearPlane = false;
    
    enum CameraMode
    {
        Idle,
        Rotate,
        Translate,
        Zoom
    } _cameraMode;
    bool _showCameras, _showGrid;
};

} // namespace
