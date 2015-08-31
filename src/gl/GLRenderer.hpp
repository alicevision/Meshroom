#pragma once

#include <QOpenGLFunctions_3_2_Core>
#include "GLDrawable.hpp"
#include "GLSLColoredShader.hpp"
#include "GLSLPlainColorShader.hpp"
#include <QObject>
#include <QColor>

namespace mockup
{

class GLView; // forward declaration
class GLPointCloud;

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
    void addAlembicScene(const QString& scene);

public slots:
    void draw();

private:
    void updateWorldMatrix();

private:
    QMatrix4x4 _cameraMat;
    GLSLColoredShader* _coloredShader = nullptr;
    GLSLPlainColorShader* _plainColorShader = nullptr;
    QSize _viewportSize;

    // Simple scene as a list of drawable objects
    QList<GLDrawable *> _scene;

};

} // namespace
