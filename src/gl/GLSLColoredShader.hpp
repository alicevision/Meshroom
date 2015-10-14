#pragma once

#include <QOpenGLShaderProgram>

namespace meshroom
{

class GLSLColoredShader : public QOpenGLShaderProgram
{

public:
    GLSLColoredShader();
    ~GLSLColoredShader() = default;

public:
    void setWorldMatrix(const QMatrix4x4& worldMat);
};

} // namespace
