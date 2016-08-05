#include <vector>
#include "GLAligner.hpp"

namespace meshroom
{

GLAligner::GLAligner()
    : GLDrawable(*_colorUniform)
    , _positionBuffer(QOpenGLBuffer::VertexBuffer)
    , _planeDefined(false)
    , _distanceDefined(false)
{
  _vao.create();
  _positionBuffer.create();

  _vao.bind();
  _positionBuffer.setUsagePattern(QOpenGLBuffer::StaticDraw);
  _positionBuffer.bind();
  _program.enableAttributeArray("in_position");
  _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
  _program.setAttributeValue("color", 1.0f, 1.0f, 0.5f, 1.0f);
  _vao.release();
  _positionBuffer.release();
}

void GLAligner::draw()
{
    _program.bind();
    _vao.bind();
    
    glLineWidth(3.0);

    if (_planeDefined) {
      glDrawArrays(GL_TRIANGLES, 0, _planePositions.size()-2);
      glDrawArrays(GL_LINES, _planePositions.size()-2, 2);
    }
    
    if (_distanceDefined)
      glDrawArrays(GL_LINES, 0, _linePositions.size());
    
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
}

void GLAligner::setPlane(const QVector3D& normal, const QVector3D& origin)
{
  _normal = normal.normalized();
  _origin = origin;
  buildPlane(0.5, 4);
  setBuffer();
  _planeDefined = true;
}


void GLAligner::setDistanceLine(const QVector3D& p0, const QVector3D& p1)
{
  _linePositions.clear();
  _linePositions.push_back(p0);
  _linePositions.push_back(p1);
  setBuffer();
  _distanceDefined = true;
}

void GLAligner::clearPlane()
{
  _planeDefined = false;
}

void GLAligner::clearDistanceLine()
{
  _distanceDefined = false;
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
  
  // Normal; length 0.25
  _planePositions.push_back(_origin);
  _planePositions.push_back(_origin + _normal*0.25f);
}


} // namespace
