#pragma once

#include <QOpenGLFunctions_3_2_Core>
#include "GLScene.hpp"
#include <QObject>
#include <QColor>

namespace meshroom
{

class GLView;
class GLPointCloud;
class GLSLBackgroundShader;

class GLRenderer : public QObject
{
    Q_OBJECT

public:
    GLRenderer();
    ~GLRenderer();

public:
    void setViewportSize(const QSize& size);
    void setCameraMatrix(const QMatrix4x4& cameraMat);
    void setClearColor(const QColor& color);
    void addAlembicScene(const QUrl& url);
    void resetScene();
    void setShowCameras(bool v);

public slots:
    void draw();

private:
    void updateWorldMatrix();

private:
    QMatrix4x4 _cameraMat;
    QSize _viewportSize;
    GLScene _scene;                    // Simple scene: a list of drawable objects
    GLSLBackgroundShader* _background; // Keep background drawing outside the scene
};

} // namespace
