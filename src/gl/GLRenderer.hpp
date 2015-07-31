#pragma once

#include <QOpenGLFunctions_3_2_Core>
#include "GLGizmo.hpp"
#include "GLGrid.hpp"
#include "GLSLColoredShader.hpp"
#include "GLSLPlainColorShader.hpp"
#include <QObject>
#include <QColor>

namespace mockup
{

class GLView; // forward declaration

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

public slots:
    void draw();

private:
    void updateWorldMatrix();

private:
    QMatrix4x4 _cameraMat;
    GLGizmo* _gizmo = nullptr;
    GLGrid* _grid = nullptr;
    GLSLColoredShader* _coloredShader = nullptr;
    GLSLPlainColorShader* _plainColorShader = nullptr;
    QSize _viewportSize;
};

} // namespace
