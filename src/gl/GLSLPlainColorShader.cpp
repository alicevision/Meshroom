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

namespace mockup
{

GLSLPlainColorShader::GLSLPlainColorShader(const QVector4D& color)
    : _color(color)
{
    _program.addShaderFromSourceCode(QOpenGLShader::Vertex, vertex_shader);
    _program.addShaderFromSourceCode(QOpenGLShader::Fragment, fragment_shader);
    _program.link();
    _program.release();
    setColor(color);
}

QOpenGLShaderProgram& GLSLPlainColorShader::program()
{
    return _program;
}

void GLSLPlainColorShader::setWorldMatrix(const QMatrix4x4& worldMat)
{
    _program.bind();
    _program.setUniformValue(_program.uniformLocation("mvpMatrix"), worldMat);
    _program.release();
}

void GLSLPlainColorShader::setColor(const QVector4D& color)
{
    _color = color;
    _program.bind();
    _program.setUniformValue(_program.uniformLocation("color"), _color);
    _program.release();
}

void GLSLPlainColorShader::bind()
{
    _program.bind();
}

void GLSLPlainColorShader::release()
{
    _program.release();
}

} // namespace
