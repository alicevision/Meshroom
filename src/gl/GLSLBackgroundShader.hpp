#pragma once

#include <QOpenGLShaderProgram>
#include <QOpenGLVertexArrayObject>

namespace mockup
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
