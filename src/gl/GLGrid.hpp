#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
#include <QOpenGLShaderProgram>

namespace mockup
{

class GLGrid
{

public:
    GLGrid(QOpenGLShaderProgram& program);
    ~GLGrid() = default;

public:
    void draw();

private:
    QOpenGLVertexArrayObject _vao;
    QOpenGLBuffer _positionBuffer;
    QOpenGLShaderProgram& _program;
    size_t _verticeCount = 0;
};

} // namespace
