#pragma once

#include <QQuickPaintedItem>
#include <QMatrix4x4>
#include <QFont>
#include "models/Camera.hpp"

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
    Q_PROPERTY(SelectionMode selectionMode MEMBER _selectionMode NOTIFY selectionModeChanged)
    Q_PROPERTY(float scale READ getScale WRITE defineScale NOTIFY scaleChanged)
    Q_PROPERTY(float yrot READ getYRot WRITE defineYRot NOTIFY yrotChanged)

public:
  
    enum SelectionMode { LINE, RECTANGLE };
    Q_ENUM(SelectionMode)
  
    GLView();
    ~GLView();

    bool showCameras() const;
    void setShowCameras(bool v);
    bool showGrid() const;
    void setShowGrid(bool v);
    void paint(QPainter*) override;
    float getScale() const { return _scale; }
    const QColor& color() const { return _color; }
    float getYRot() const { return _yrotDegrees; }

public slots:
    void setColor(const QColor& color);
    void loadAlembicScene(const QUrl& url);
    void definePlane();
    void clearPlane();
    void flipPlaneNormal();
    void defineYRot(float degrees);
    void defineScale(float scale);
    void resetScale();

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
    void selectionModeChanged();
    void scaleChanged();
    void yrotChanged();

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
    
    // Functions to manipulate the rotation.
    void handleYRotMousePressEvent(QMouseEvent*);
    void handleYRotMouseMoveEvent(QMouseEvent*);

private:
    // Delegate opengl rendering
    GLRenderer* _renderer = nullptr;
    QRect _viewport;
    QColor _color;
    Camera _camera;
    QUrl _alembicSceneUrl;
    QFont _font;
    
    // FIXME : rename variables to something more meaningful
    // Ideally the following variables should go in a manipulator of some sort
    QPoint _mousePos;      // Position of the mousePressed event
    QMatrix4x4 _camMatTmp; // Position of the camera when the mouse is pressed
    QVector3D _lookAtTmp;
    
    // Selection handling.
    SelectionMode _selectionMode = RECTANGLE;
    QPoint _selectedP0, _selectedP1;
    QRect _selectedArea;
    bool _clearSelection = false;
    const std::vector<QVector3D>* _selectedPoints;  // owned by the renderer!
    QRect getSelectionRect() const;

    QVector3D _planeNormal;
    QVector3D _planeOrigin;
    QVector3D _distanceLine[2];
    float _scale = 1.0f;
    float _yrotDegrees = 0.0f;
    bool _planeDefined = false;
    bool _clearPlane = false;
    bool _scaleDefined = false;
    bool _clearScale = false;
    
    enum CameraMode
    {
        Idle,
        Rotate,
        Translate,
        Zoom
    } _cameraMode = Idle;
    
    bool _showCameras, _showGrid;
};

} // namespace
