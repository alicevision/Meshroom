#include "GLSLColoredShader.hpp"
#include <QMatrix4x4>

namespace
{

const GLchar* vertex_shader = R"(#version 330
        in vec3 in_position;
        in vec3 in_color;
        out vec3 ex_color;
        uniform mat4 mvpMatrix;
        void main(void) {
            gl_Position = mvpMatrix*vec4(in_position.xyz, 1.0);
            ex_color = in_color;
        })";

const GLchar* fragment_shader = R"(#version 330
        in vec3 ex_color;
        layout (location = 0) out vec4 frag_color;
        void main(void) {
            frag_color = vec4(ex_color, 1.0);
        })";

} // namespace

namespace mockup
{

GLSLColoredShader::GLSLColoredShader()
{
    // shader compilation
    _program.addShaderFromSourceCode(QOpenGLShader::Vertex, vertex_shader);
    _program.addShaderFromSourceCode(QOpenGLShader::Fragment, fragment_shader);
    _program.link();
    _program.release();
}

QOpenGLShaderProgram& GLSLColoredShader::program()
{
    return _program;
}

void GLSLColoredShader::setWorldMatrix(const QMatrix4x4& worldMat)
{
    _program.bind();
    _program.setUniformValue(_program.uniformLocation("mvpMatrix"), worldMat);
    _program.release();
}

void GLSLColoredShader::bind()
{
    _program.bind();
}

void GLSLColoredShader::release()
{
    _program.release();
}

} // namespace
