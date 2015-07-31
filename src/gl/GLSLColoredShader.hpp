#pragma once

#include <QOpenGLShaderProgram>

namespace mockup
{

class GLSLColoredShader
{

public:
    GLSLColoredShader();
    ~GLSLColoredShader() = default;

public:
    QOpenGLShaderProgram& program();
    void setWorldMatrix(const QMatrix4x4& worldMat);
    void bind();
    void release();

private:
    QOpenGLShaderProgram _program;
};

} // namespace
