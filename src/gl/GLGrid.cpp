#include "GLGrid.hpp"
#include <QVector>

namespace mockup
{

namespace // empty namespace
{

void buildGridData(QVector<float>& griddata, float first, float last, float offset)
{
    for(float i=first; i<=last; i+=offset)
    {
        griddata.append(i);
        griddata.append(0.f);
        griddata.append(first);

        griddata.append(i);
        griddata.append(0.f);
        griddata.append(last);

        griddata.append(first);
        griddata.append(0.f);
        griddata.append(i);

        griddata.append(last);
        griddata.append(0.f);
        griddata.append(i);
    }
}

} // empty namespace



GLGrid::GLGrid(QOpenGLShaderProgram& program)
    : _positionBuffer(QOpenGLBuffer::VertexBuffer)
    , _program(program)
{
    _vao.create();
    _vao.bind();

    QVector<float> positionData;
    buildGridData(positionData, -10.f, 10.f, 1.f);
    _verticeCount = positionData.count();

    _positionBuffer.create();
    _positionBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
    _positionBuffer.bind();
    _positionBuffer.allocate(positionData.data(), _verticeCount * sizeof(float));
    _program.enableAttributeArray("in_position");
    _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
    _positionBuffer.release();

    _vao.release();
}

void GLGrid::draw()
{
    _program.bind();
    _vao.bind();
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
    glDrawArrays(GL_LINES, 0, _verticeCount);
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    _vao.release();
    _program.release();
}

} // namespace
