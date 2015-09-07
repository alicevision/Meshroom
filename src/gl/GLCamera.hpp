#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>
#include "GLDrawable.hpp"

// GLCamera Gizmo
// draw a simple camera

namespace mockup
{

class GLCamera : public GLDrawable
{

public:
    GLCamera();
    ~GLCamera() = default;

    void draw() override;
    void setProjectionMatrix(const QMatrix4x4 &mat) {_projectionMatrix = mat;}

private:
    QOpenGLVertexArrayObject _vao;
    QMatrix4x4 _projectionMatrix;

    static QVector<float> _cameraMesh;
    static QVector<float> _cameraMeshColors;
};

} // namespace
