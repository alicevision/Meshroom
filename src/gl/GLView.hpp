#pragma once

#include <QtQuick/QQuickItem>

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

private:
    GLRenderer* _renderer = nullptr;
    QRect _rect;
    QColor _color;
    QObject* _camera = nullptr;
};

} // namespace
