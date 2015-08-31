#include "GLCamera.hpp"
#include <QVector>

namespace mockup
{


GLCamera::GLCamera(QOpenGLShaderProgram& program)
    : _positionBuffer(QOpenGLBuffer::VertexBuffer)
    , _program(program)
    , _position(0.0, 0.0, 0.0)
{
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

void GLCamera::setPosition(const QVector3D& v)
{
    _position = v;
}

QMatrix4x4 GLCamera::modelMatrix() const
{
    QMatrix4x4 modelMat;
    modelMat.translate(_position);

    return modelMat;
}

} // namespace

