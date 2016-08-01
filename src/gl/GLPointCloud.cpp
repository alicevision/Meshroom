#include "GLPointCloud.hpp"
#include "io/AlembicImport.hpp"
#include <iostream>

namespace meshroom
{

GLPointCloud::GLPointCloud()
    : GLDrawable(*_colorArray)
    , _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _selectedPositions(QOpenGLBuffer::VertexBuffer)
    , _pointColors(QOpenGLBuffer::VertexBuffer)
    , _npoints(0)
{
    _vertexArrayObject.create();
    _selectionVAO.create();
}

void GLPointCloud::setRawPositions(const void* pointsBuffer, size_t npoints)
{
    // Allow only one load
    if(_npoints != 0)
        return;
    
    {
      const float* src = static_cast<const float*>(pointsBuffer);
      _rawPositions.resize(npoints);
      for (size_t i = 0; i < npoints; ++i, src += 3)
        _rawPositions[i] = QVector3D(src[0], src[1], src[2]);
    }
    

    _vertexArrayObject.bind();
    if(_pointPositions.create())
    {
        _pointPositions.setUsagePattern(QOpenGLBuffer::StaticDraw);
        _pointPositions.bind();
        _npoints = npoints;
        _pointPositions.allocate(pointsBuffer, npoints * 3 * sizeof(float));
        glPointSize(1);
        _program.enableAttributeArray("in_position");
        _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
        _pointPositions.release();
    }
    else
    {
        std::cout << "unable to create buffer for point cloud" << std::endl;
    }
    _vertexArrayObject.release();
}

void GLPointCloud::setRawColors(const void* pointsBuffer, size_t npoints)
{
    _vertexArrayObject.bind();
    if(_pointColors.create())
    {
        _pointColors.setUsagePattern(QOpenGLBuffer::StaticDraw);
        _pointColors.bind();
        _pointColors.allocate(pointsBuffer, npoints * 3 * sizeof(float));
        _program.enableAttributeArray("in_color");
        _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
        _pointColors.release();
    }
    else
    {
        std::cout << "unable to create buffer for point cloud" << std::endl;
    }
    _vertexArrayObject.release();
}

void GLPointCloud::selectPoints(const QRectF& selection, const QRectF& viewport)
{
  std::vector<QVector3D> selectedPositions;
  
  for (const auto& p: _rawPositions)
  if (pointSelected(p, selection, viewport))
    selectedPositions.push_back(p);

  _nselected = (GLint)selectedPositions.size();
  
  // VAO setup needs to be done only once.
  if (!_selectedPositions.isCreated()) {
    _selectedPositions.create();
    _selectedPositions.setUsagePattern(QOpenGLBuffer::DynamicDraw);

    _selectionVAO.bind();
    _selectedPositions.bind();
    _program.enableAttributeArray("in_position");
    _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
    // Static color for selected points
    _program.disableAttributeArray("in_color");
    _program.setAttributeValue("in_color", 1, 0.2, 0.8);
    _selectionVAO.release();
  }

  _selectedPositions.bind();
  _selectedPositions.allocate(selectedPositions.data(), selectedPositions.size()*3*sizeof(float));
  _selectedPositions.release();
}

// NOTE: _cameraMatrix is static and is actually the MVP matrix used for rendering
bool GLPointCloud::pointSelected(const QVector3D& point, const QRectF& selection, const QRectF& viewport)
{
  // UGLY HACK; WIP
  return ((size_t)(&point) >> 8) & 1;
}

void GLPointCloud::draw()
{
  _program.bind();
  
  if (_npoints) {
    _vertexArrayObject.bind();
    glPointSize(1.0f);
    glDrawArrays(GL_POINTS, 0, _npoints);
    _vertexArrayObject.release();
  }
  
  // We're overdrawing, so need to disable depth test.
  if (_nselected) {
    glDisable(GL_DEPTH_TEST);
    _selectionVAO.bind();
    glPointSize(2.0f);
    glDrawArrays(GL_POINTS, 0, _nselected);
    _selectionVAO.release();
    glEnable(GL_DEPTH_TEST);
  }
  
  _program.release();
}

} // namespace
