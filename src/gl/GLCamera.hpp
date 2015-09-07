#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
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
    QOpenGLBuffer _positionBuffer;
    QMatrix4x4 _projectionMatrix;
};

}
