#pragma once

#include <QOpenGLShaderProgram>
#include <QOpenGLVertexArrayObject>

namespace meshroom
{

class GLSLBackgroundShader : public QOpenGLShaderProgram
{

public:
    GLSLBackgroundShader();
    ~GLSLBackgroundShader() = default;

    void draw();

private:
    QOpenGLVertexArrayObject _vao;
};

} // namespace
