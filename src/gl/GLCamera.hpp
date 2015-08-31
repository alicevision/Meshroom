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

public:
    void draw() override;
    QMatrix4x4 modelMatrix() const;

    void setPosition(const QVector3D& v);
    //
    //
    void setModelMatrix(const QMatrix4x4 &);
    // TODO : set Matrix

private:
    QOpenGLVertexArrayObject _vao;
    QOpenGLBuffer _positionBuffer;
    QOpenGLShaderProgram& _program;
    QVector3D _position;
};

}
