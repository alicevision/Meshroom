#include "GLCamera.hpp"
#include <QVector>
#include <QOpenGLBuffer>

namespace meshroom
{

// GL_LINES
QVector<float> GLCamera::_cameraMesh{
    0.f,  0.f,  0.f,  0.5,  0.f,  0.f,  0.f,  0.f,  0.f,  0.f,  0.5,  0.f,  0.f, 0.f,
    0.f,  0.f,  0.f,  0.5,  0.f,  0.f,  0.f,  -0.3, 0.2,  -0.3, 0.f,  0.f,  0.f, -0.3,
    -0.2, -0.3, 0.f,  0.f,  0.f,  0.3,  -0.2, -0.3, 0.f,  0.f,  0.f,  0.3,  0.2, -0.3,
    -0.3, 0.2,  -0.3, -0.3, -0.2, -0.3, -0.3, -0.2, -0.3, 0.3,  -0.2, -0.3, 0.3, -0.2,
    -0.3, 0.3,  0.2,  -0.3, 0.3,  0.2,  -0.3, -0.3, 0.2,  -0.3};

QVector<float> GLCamera::_cameraMeshColors{
    1.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f,
    1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f,
    1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f,
    1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f, 1.f};

GLCamera::GLCamera()
    : GLDrawable(*_colorArray)
{
    _projectionMatrix.perspective(60.0f, 3.0 / 2.0, 0.1f, 100.0f);
    _vao.create();
    _vao.bind();

    QOpenGLBuffer positions(QOpenGLBuffer::VertexBuffer);
    positions.create();
    positions.setUsagePattern(QOpenGLBuffer::StaticDraw);
    positions.bind();
    positions.allocate(_cameraMesh.data(), _cameraMesh.size() * sizeof(float));
    _program.enableAttributeArray("in_position");
    _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
    positions.release();

    QOpenGLBuffer colors;
    colors.create();
    colors.setUsagePattern(QOpenGLBuffer::StaticDraw);
    colors.bind();
    colors.allocate(_cameraMeshColors.data(), _cameraMeshColors.size() * sizeof(float));
    _program.enableAttributeArray("in_color");
    _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
    colors.release();

    _vao.release();
}

void GLCamera::draw()
{
    _program.bind();
    _vao.bind();
    glDrawArrays(GL_LINES, 0, _cameraMesh.size() / 3);
    _vao.release();
    _program.release();
}

} // namespace
