#include "GLSLPlainColorShader.hpp"
#include <QMatrix4x4>

namespace
{

const GLchar* vertex_shader = R"(#version 330
        in vec3 in_position;
        uniform mat4 mvpMatrix;
        void main(void) {
            gl_Position = mvpMatrix*vec4(in_position.xyz, 1.0);
        })";

const GLchar* fragment_shader = R"(#version 330
        layout (location = 0) out vec4 frag_color;
        uniform vec4 color;
        void main(void) {
            frag_color = vec4(color);
        })";

} // namespace

namespace meshroom
{

GLSLPlainColorShader::GLSLPlainColorShader(const QVector4D& color)
    : QOpenGLShaderProgram()
    , _color(color)
{
    addShaderFromSourceCode(QOpenGLShader::Vertex, vertex_shader);
    addShaderFromSourceCode(QOpenGLShader::Fragment, fragment_shader);
    link();
    release();
    setColor(color);
}

void GLSLPlainColorShader::setWorldMatrix(const QMatrix4x4& worldMat)
{
    bind();
    setUniformValue(uniformLocation("mvpMatrix"), worldMat);
    release();
}

void GLSLPlainColorShader::setColor(const QVector4D& color)
{
    _color = color;
    bind();
    setUniformValue(uniformLocation("color"), _color);
    release();
}

} // namespace
