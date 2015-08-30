#include "GLPointCloud.hpp"
#include "io/AlembicImport.hpp"

namespace mockup
{

GLPointCloud::GLPointCloud(QOpenGLShaderProgram& program, const QString& cloud)
    : _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _npoints(0)
    , _program(program)
{
    if(_vertexArrayObject.create())
    {
        _vertexArrayObject.bind();
        if(_pointPositions.create())
        {
            _pointPositions.setUsagePattern(QOpenGLBuffer::StaticDraw);
            _pointPositions.bind();
            // Load alembic point cloud
            // FIXME: importer shouldn't be in this function but rather outside and contructing a
            // GLPointCloud
            AlembicImport importer(cloud.toStdString().c_str());
            // FIXME
            _npoints = importer.pointCloudSize();
            _pointPositions.allocate(importer.pointCloudData(),
                                     importer.pointCloudSize() * 3 * sizeof(float));
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
    _program.bind();
    _vertexArrayObject.bind();
    glDrawArrays(GL_POINTS, 0, _npoints);
    _vertexArrayObject.release();
    _program.release();
}

// template <>
// GLPointCloud* GLPointCloud::createFrom(const int& importer)
// {
// }

} // namespace
