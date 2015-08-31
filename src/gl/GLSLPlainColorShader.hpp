#pragma once

#include <QOpenGLShaderProgram>

namespace mockup
{

class GLSLPlainColorShader : public QOpenGLShaderProgram
{

public:
    GLSLPlainColorShader(const QVector4D& color = QVector4D(1, 0, 1, 1));
    ~GLSLPlainColorShader() = default;

public:
    void setWorldMatrix(const QMatrix4x4& worldMat);
    void setColor(const QVector4D& color);

private:
    QVector4D _color;
};

} // namespace
