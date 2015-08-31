#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
#include <QOpenGLShaderProgram>
#include "GLDrawable.hpp"

namespace mockup
{

class GLGizmo : public GLDrawable
{

public:
    GLGizmo(QOpenGLShaderProgram& program);
    ~GLGizmo() = default;

public:
    void draw() override;
    QMatrix4x4 modelMatrix() const;

    void setPosition(const QVector3D& v);

private:
    QOpenGLVertexArrayObject _vao;
    QOpenGLBuffer _positionBuffer;
    QOpenGLBuffer _colorBuffer;
    QOpenGLShaderProgram& _program;
    QVector3D _position;
};

} // namespace
