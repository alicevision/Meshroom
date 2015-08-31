#pragma once

#include <QtQuick/QQuickItem>
#include <QMatrix4x4>
namespace mockup
{
// forward declaration
class GLRenderer;
class CameraModel;

class GLView : public QQuickItem
{
    Q_OBJECT
    Q_PROPERTY(QColor color READ color WRITE setColor NOTIFY colorChanged)
    Q_PROPERTY(QObject* camera READ camera WRITE setCamera NOTIFY cameraChanged)

public:
    GLView();
    ~GLView();

public slots:
    const QColor& color() const;
    void setColor(const QColor& color);
    QObject * camera() const;
    void setCamera(QObject* camera);
    void setPointCloud(const QString& cloud);

private slots:
    void handleWindowChanged(QQuickWindow* win);
    void sync();
    void paint();
    void refresh();

signals:
    void colorChanged();
    void cameraChanged();

protected:
    void mouseMoveEvent(QMouseEvent*);
    void mousePressEvent(QMouseEvent*);
    void mouseReleaseEvent(QMouseEvent*);
    void wheelEvent(QWheelEvent* event);

    // Function to manipulate cameras. 
    // might move in a different class, eg CameraManipulator
    void trackBallRotateCamera(QMatrix4x4 &cam, const QVector3D &lookAt, float dx, float dy);
    void turnTableRotateCamera(QMatrix4x4 &cam, const QVector3D &lookAt, float dx, float dy);
    void planeTranslateCamera(QMatrix4x4 &cam, float dx, float dy);
    void translateLineOfSightCamera(QMatrix4x4 &cam, float &radius, float dx, float dy);

private:
    GLRenderer* _renderer = nullptr;
    QRect _rect;
    QColor _color;
    CameraModel * _camera = nullptr;
    QString _pointCloud;

    /// FIXME : rename variables to something more meaningful
    QPoint _pressedPos;      /// Position of the mousePressed event
    QMatrix4x4 _cameraBegin; /// Position of the camera when the mouse is pressed
    QVector3D _lookAt;
    enum CameraMode
    {
        Idle,
        Rotate,
        Translate,
        Zoom
    } _cameraMode;
};

} // namespace
