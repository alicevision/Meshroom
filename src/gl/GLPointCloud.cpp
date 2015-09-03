#include "GLPointCloud.hpp"
#include "io/AlembicImport.hpp"
#include <iostream>

namespace mockup
{

GLPointCloud::GLPointCloud()
    : _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _npoints(0)
    , _program(*_colorUniform)
{}

void GLPointCloud::setRawData(const void *pointsBuffer, size_t npoints)
{
    // Allow only one load
    if (_npoints != 0) return;

    if(_vertexArrayObject.create())
    {
        _vertexArrayObject.bind();
        if(_pointPositions.create())
        {
            _pointPositions.setUsagePattern(QOpenGLBuffer::StaticDraw);
            _pointPositions.bind();
            _npoints = npoints;
            _pointPositions.allocate(pointsBuffer, npoints * 3 * sizeof(float));
            _program.enableAttributeArray("in_position");
            _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
            _pointPositions.release();
            _vertexArrayObject.release();
        }
        else
        {
            std::cout << "unable to create buffer for point cloud" << std::endl;
        }
    }
    else
    {
        std::cout << "unable to create VAO for point cloud" << std::endl;
    }
}


void GLPointCloud::draw()
{
    if (_npoints)
    {
        _program.bind();
        _vertexArrayObject.bind();
        glDrawArrays(GL_POINTS, 0, _npoints);
        _vertexArrayObject.release();
        _program.release();
    }
}

} // namespace
