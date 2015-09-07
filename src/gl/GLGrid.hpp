#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
#include <QOpenGLShaderProgram>
#include "GLDrawable.hpp"

namespace mockup
{

class GLGrid : public GLDrawable
{

public:
    GLGrid();
    ~GLGrid() = default;

public:
    void draw() override;

private:
    QOpenGLVertexArrayObject _vao;
    QOpenGLBuffer _positionBuffer;
    size_t _verticeCount = 0;
};

} // namespace
