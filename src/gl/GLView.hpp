#pragma once

#include <QtQuick/QQuickItem>
#include <QMatrix4x4>
namespace mockup
{

class GLRenderer; // forward declaration

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
    QObject* camera() const;
    void setCamera(QObject* camera);

private slots:
    void handleWindowChanged(QQuickWindow* win);
    void sync();
    void paint();
    void refresh();

signals:
    void colorChanged();
    void cameraChanged();

protected:
    void mouseMoveEvent(QMouseEvent *);
    void mousePressEvent(QMouseEvent *);
    void mouseReleaseEvent(QMouseEvent *);

private:
    GLRenderer* _renderer = nullptr;
    QRect _rect;
    QColor _color;
    QObject* _camera = nullptr;

    /// FIXME : rename variables
    QPoint _pressedPos;         /// Position of the mousePressed event
    QMatrix4x4  _cameraBegin;   /// Position of the camera when the mouse is pressed   
    QVector3D _lookAt;
    enum CameraMode {Idle, Rotate, Translate, Zoom} _cameraMode;
};

} // namespace
