#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
#include "GLDrawable.hpp"

namespace meshroom
{

class GLGizmo : public GLDrawable
{

public:
    GLGizmo();
    ~GLGizmo() = default;

public:
    void draw() override;

private:
    QOpenGLVertexArrayObject _vao;
    QOpenGLBuffer _positionBuffer;
    QOpenGLBuffer _colorBuffer;
};

} // namespace
