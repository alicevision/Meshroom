#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLBuffer>
#include <QOpenGLShaderProgram>
#include <QVector3D>
#include "GLDrawable.hpp"

namespace meshroom
{

class GLAligner : public GLDrawable
{

public:
  GLAligner();
  ~GLAligner() = default;

  void draw() override;
  void setPlane(const QVector3D& normal, const QVector3D& origin);
  void clearPlane();
  void setDistanceLine(const QVector3D& p0, const QVector3D& p1);
  void clearDistanceLine();

private:
  void buildPlane(float size, int division);
  void setBuffer();
  
  QVector3D _normal;
  QVector3D _origin;
  
  QOpenGLVertexArrayObject _vao;
  QOpenGLBuffer _positionBuffer;
  std::vector<QVector3D> _planePositions, _linePositions;
  
  bool _planeDefined;
  bool _distanceDefined;
};

} // namespace
