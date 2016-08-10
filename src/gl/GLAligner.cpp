#include <vector>
#include "GLAligner.hpp"

namespace meshroom
{

GLAligner::GLAligner()
    : GLDrawable(*_colorArray)
    , _positionBuffer(QOpenGLBuffer::VertexBuffer)
    , _colorBuffer(QOpenGLBuffer::VertexBuffer)
{
  _vao.create();
  
  _positionBuffer.create();
  _positionBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
  
  _colorBuffer.create();
  _colorBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
  
  _vao.bind();
  
  _positionBuffer.bind();
  _program.enableAttributeArray("in_position");
  _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
  
  _colorBuffer.bind();
  _program.enableAttributeArray("in_color");
  _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
  
  _vao.release();
  _positionBuffer.release();
  _colorBuffer.release();
}

void GLAligner::draw()
{
    _program.bind();
    _vao.bind();
    
    glDisable(GL_LINE_SMOOTH);
    glLineWidth(3.0);

    if (!_planePositions.empty()) {
      glDrawArrays(GL_TRIANGLES, 0, _planePositions.size()-6);
      glDrawArrays(GL_LINES, _planePositions.size()-6, 6);
    }
    
    if (!_linePositions.empty())
      glDrawArrays(GL_LINES, _planePositions.size(), _linePositions.size());
    
    _vao.release();
    _program.release();
}

void GLAligner::setBuffer()
{
  _positionBuffer.bind();
  _positionBuffer.allocate((_planePositions.size()+_linePositions.size())*sizeof(QVector3D));
  if (!_planePositions.empty())
    _positionBuffer.write(0, _planePositions.data(), _planePositions.size()*sizeof(QVector3D));
  if (!_linePositions.empty())
    _positionBuffer.write(_planePositions.size()*sizeof(QVector3D), _linePositions.data(), _linePositions.size()*sizeof(QVector3D));
  _positionBuffer.release();
  
  _colorBuffer.bind();
  _colorBuffer.allocate((_planePositions.size()+_linePositions.size())*sizeof(QVector3D));
  if (!_planePositions.empty())
    _colorBuffer.write(0, _planeColors.data(), _planePositions.size()*sizeof(QVector3D));
  if (!_linePositions.empty())
    _colorBuffer.write(_planePositions.size()*sizeof(QVector3D), _lineColors.data(), _linePositions.size()*sizeof(QVector3D));
  _colorBuffer.release();
}

void GLAligner::setPlane(const QVector3D& normal, const QVector3D& origin)
{
  _normal = normal.normalized();
  _origin = origin;
  buildPlane(0.5, 4);
  setBuffer();
}

static const QVector3D MARKER_COLOR = QVector3D(224, 255, 0) / 255.f;

void GLAligner::setDistanceLine(const QVector3D& p0, const QVector3D& p1)
{
  _linePositions.clear();
  _linePositions.push_back(p0); _lineColors.push_back(MARKER_COLOR);
  _linePositions.push_back(p1); _lineColors.push_back(MARKER_COLOR);
  setBuffer();
}

void GLAligner::clearPlane()
{
  _planePositions.clear();
  _planeColors.clear();
}

void GLAligner::clearDistanceLine()
{
  _linePositions.clear();
  _lineColors.clear();
}

void GLAligner::buildPlane(float size, int division)
{
  const QVector3D U = QVector3D(-_normal[2], 0, _normal[0]).normalized();
  const QVector3D V = QVector3D::crossProduct(U, _normal).normalized();
  
  
  const auto point = [=](int i, int j)
  {
    float u = size*i/division;
    float v = size*j/division;
    return _origin + u*U + v*V;
  };
  
  _planePositions.clear();
  _planeColors.clear();
  
  // Plane
  for (int i = -division; i < division; ++i)
  for (int j = -division; j < division; ++j)
  {
    auto p0 = point(i, j);
    auto p1 = point(i+1, j);
    auto p2 = point(i+1, j+1);
    auto p3 = point(i, j+1);
    
    _planePositions.push_back(p0);
    _planePositions.push_back(p1);
    _planePositions.push_back(p2);

    _planePositions.push_back(p0);
    _planePositions.push_back(p2);
    _planePositions.push_back(p3);
  }
  
  _planeColors.resize(_planePositions.size(), MARKER_COLOR);
  
  // Axes: length 0.25; note XZ are arbitrary; must compute proper transformation
  // X
  _planePositions.push_back(_origin); _planeColors.push_back(QVector3D(1, 0, 0));
  _planePositions.push_back(_origin + U*0.25f); _planeColors.push_back(QVector3D(1, 0, 0));
  // Y
  _planePositions.push_back(_origin); _planeColors.push_back(QVector3D(0, 1, 0));
  _planePositions.push_back(_origin + _normal*0.25f); _planeColors.push_back(QVector3D(0, 1, 0));
  // Z
  _planePositions.push_back(_origin); _planeColors.push_back(QVector3D(0, 0, 1));
  _planePositions.push_back(_origin + V*0.25f); _planeColors.push_back(QVector3D(0, 0, 1));
  
}


} // namespace
