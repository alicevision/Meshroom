#include "GLCamera.hpp"
#include <QVector>

namespace mockup
{

GLCamera::GLCamera()
    : GLDrawable(*_colorArray)
    , _positionBuffer(QOpenGLBuffer::VertexBuffer)
{
    _projectionMatrix.perspective(60.0f, 3.0/2.0, 0.1f, 100.0f);

    _vao.create();
    _vao.bind();

    QVector<float> positionData{0.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 0.f, 0.f,
                                0.f, 1.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 1.f};
    _positionBuffer.create();
    _positionBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
    _positionBuffer.bind();
    _positionBuffer.allocate(positionData.data(), 6 * 3 * sizeof(float));
    _program.enableAttributeArray("in_position");
    _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
    _positionBuffer.release();

    QVector<float> colorData{1.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f,
                             0.f, 1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f, 1.f};
    QOpenGLBuffer _colorBuffer;
    _colorBuffer.create();
    _colorBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
    _colorBuffer.bind();
    _colorBuffer.allocate(colorData.data(), 6 * 3 * sizeof(float));
    _program.enableAttributeArray("in_color");
    _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
    _colorBuffer.release();

    _vao.release();
}

void GLCamera::draw()
{
    _program.bind();
    _vao.bind();
    glDrawArrays(GL_LINES, 0, 6);
    _vao.release();
    _program.release();
}


} // namespace
