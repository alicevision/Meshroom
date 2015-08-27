#include "GLPointCloud.hpp"
#include "io/AlembicImport.hpp"

namespace mockup {

GLPointCloud::GLPointCloud(QOpenGLShaderProgram &program)
    : _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _npoints(0)
    , _program(program)
{
    //
    
    // DUMMY point grid
    float *dummyPoints = new float[3000]; // 1000 points
    for (int i=0; i<3000; i++) {
        dummyPoints[i] = 20*(0.5-static_cast<float>(rand())/RAND_MAX); 
    }

    // TODO create
    if(_vertexArrayObject.create()) {
        _vertexArrayObject.bind();
        if(_pointPositions.create()) {
            _pointPositions.setUsagePattern(QOpenGLBuffer::StaticDraw);
            _pointPositions.bind();
            // Load alembic point cloud
            // FIXME: importer shouldn't be in this function but rather outside and contructing a GLPointCloud
            AlembicImport importer("/datas/pih/develop/openMVG.pih/tests/reconstruction/test_47.abc"); 
            // FIXME
            _npoints = importer.pointCloudSize();
            std::cout << "FOUND NBPOINTS:" << _npoints << std::endl;
            _pointPositions.allocate(importer.pointCloudData(), importer.pointCloudSize()*3*sizeof(float));

                
            //_npoints = 1000;
            //_pointPositions.allocate(dummyPoints, 3*_npoints*sizeof(float));
            _program.enableAttributeArray("in_position");
            _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
            _pointPositions.release();    
            _vertexArrayObject.release();
        } else {
            std::cout << "unable to create buffer for point cloud" << std::endl;
        }
    } else {
        std::cout << "unable to create VAO for point cloud" << std::endl;
    }
    delete [] dummyPoints;
}

void GLPointCloud::draw()
{
    _program.bind();
    _vertexArrayObject.bind();
    glDrawArrays(GL_POINTS, 0, _npoints);
    _vertexArrayObject.release();
    _program.release();
}


template <>
GLPointCloud* GLPointCloud::createFrom(const int &importer)
{

}


}
