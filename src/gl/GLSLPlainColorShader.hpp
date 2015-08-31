#pragma once

#include <QOpenGLShaderProgram>

namespace mockup
{

class GLSLPlainColorShader
{

public:
    GLSLPlainColorShader(const QVector4D& color = QVector4D(1, 0, 1, 1));
    ~GLSLPlainColorShader() = default;

public:
    QOpenGLShaderProgram& program();
    void setWorldMatrix(const QMatrix4x4& worldMat);
    void setColor(const QVector4D& color);
    void bind();
    void release();

private:
    QOpenGLShaderProgram _program;
    QVector4D _color;
};

} // namespace
