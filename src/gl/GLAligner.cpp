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
      glDrawArrays(GL_TRIANGLES, 0, _planeVertexCount);
      glDrawArrays(GL_LINES, _planeVertexCount, 2);
    }
    
    if (_distanceDefined)
      glDrawArrays(GL_LINES, _planeVertexCount+2, 2);
    
    _vao.release();
    _program.release();
}

void GLAligner::setPlane(const QVector3D& normal, const QVector3D& origin)
{
  _normal = normal.normalized();
  _origin = origin;
  build(0.5, 4);
  _planeDefined = true;
}


void GLAligner::setDistanceLine(const QVector3D& p0, const QVector3D& p1)
{
  _positions[_planeVertexCount+2] = p0;
  _positions[_planeVertexCount+3] = p1;
  _positionBuffer.allocate(_positions.data(), _positions.size()*sizeof(float));
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

void GLAligner::build(float size, int division)
{
  const QVector3D U = QVector3D(-_normal[2], 0, _normal[0]).normalized();
  const QVector3D V = QVector3D::crossProduct(U, _normal).normalized();
  
  const auto point = [=](int i, int j)
  {
    float u = size*i/division;
    float v = size*j/division;
    return _origin + u*U + v*V;
  };
  
  _positions.clear();
  
  // Plane
  for (int i = -division; i < division; ++i)
  for (int j = -division; j < division; ++j)
  {
    auto p0 = point(i, j);
    auto p1 = point(i+1, j);
    auto p2 = point(i+1, j+1);
    auto p3 = point(i, j+1);
    
    _positions.push_back(p0);
    _positions.push_back(p1);
    _positions.push_back(p2);

    _positions.push_back(p0);
    _positions.push_back(p2);
    _positions.push_back(p3);
  }
  _planeVertexCount = _positions.size();
  
  // Normal; length 0.25
  _positions.push_back(_origin);
  _positions.push_back(_origin + _normal*0.25f);
  
  // Distance line
  _positions.push_back(QVector3D());
  _positions.push_back(QVector3D());
  
  _positionBuffer.bind();
  _positionBuffer.allocate(_positions.data(), _positions.size()*sizeof(QVector3D));
  _positionBuffer.release();
}


} // namespace
