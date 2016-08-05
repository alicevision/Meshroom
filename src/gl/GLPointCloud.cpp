#include <float.h>
#include <math.h>
#include "GLPointCloud.hpp"

namespace meshroom
{

// Selected to avoid overflow during distance computations.
const float GLPointCloud::INF_COORD = sqrt(FLT_MAX/64);

// When isSelection is true, we're drawing the points as selection: larger size
GLPointCloud::GLPointCloud(bool isSelection)
    : GLDrawable(*_colorArray)
    , _isSelection(isSelection)
    , _pointPositions(QOpenGLBuffer::VertexBuffer)
    , _pointColors(QOpenGLBuffer::VertexBuffer)
{
    _vertexArrayObject.create();

    if (!_pointPositions.create() || !_pointColors.create()) {
      qCritical() << "cannot create buffer for point cloud positions and/or colors";
      return;
    }
    
    _pointPositions.setUsagePattern(isSelection ? QOpenGLBuffer::DynamicDraw : QOpenGLBuffer::StaticDraw);
    _pointColors.setUsagePattern(QOpenGLBuffer::StaticDraw);
    
    // VAO remembers bindings&attributes, but NOT buffer contents.
    _vertexArrayObject.bind();
    
    _pointPositions.bind();
    _program.enableAttributeArray("in_position");
    _program.setAttributeBuffer("in_position", GL_FLOAT, 0, 3);
    
    if (!_isSelection) {
      _pointColors.bind();
      _program.enableAttributeArray("in_color");
      _program.setAttributeBuffer("in_color", GL_FLOAT, 0, 3);
    }
    else {
      _program.disableAttributeArray("in_color");
      _program.setAttributeValue("in_color", 1.0f, 0.2f, 0.8f);
    }
    
    _vertexArrayObject.release();
    
    // Must be unbound after VAO.
    _pointPositions.release();
    _pointColors.release();
}

void GLPointCloud::setRawPositions(const void* pointsBuffer, size_t npoints)
{
  {
    const float* src = static_cast<const float*>(pointsBuffer);
    _rawPositions.resize(npoints);
    for (size_t i = 0; i < npoints; ++i, src += 3)
      _rawPositions[i] = QVector3D(src[0], src[1], src[2]);
  }

  _pointPositions.bind();
  _pointPositions.allocate(pointsBuffer, npoints * 3 * sizeof(float));
  _pointPositions.release();
}

void GLPointCloud::setRawColors(const void* pointsBuffer, size_t npoints)
{
  _pointColors.bind();
  _pointColors.allocate(pointsBuffer, npoints * 3 * sizeof(float));
  _pointColors.release();
}

void GLPointCloud::selectPoints(std::vector<QVector3D>& selectedPositions, const QRectF& selection, const QRectF& viewport)
{
  for (const auto& p: _rawPositions)
  if (pointSelected(p, selection, viewport))
    selectedPositions.push_back(p);
}

// Select two points nearest to p0 and p1 in screen space and nearest to the viewer.
// This will update existing data in selectedPositions.
void GLPointCloud::selectPoints(std::vector<QVector3D>& selectedPositions, const QPointF& p0, const QPointF& p1, const QRectF& viewport)
{
  float distance[2];
  
  const auto update = [&](int i, const QVector3D& p, const QPointF& target) {
    float d = screenDistance(p, target, viewport);
    if (d < distance[i]) {
      distance[i] = d;
      selectedPositions[i] = p;
    }
  };
  
  if (selectedPositions.size() != 2) {
    selectedPositions.resize(2);
    selectedPositions[0] = QVector3D(INF_COORD, INF_COORD, INF_COORD);
    selectedPositions[1] = selectedPositions[0];
    distance[0] = distance[1] = INF_COORD;
  }
  else {
    distance[0] = screenDistance(selectedPositions[0], p0, viewport);
    distance[1] = screenDistance(selectedPositions[1], p1, viewport);
  }
  
  for (const auto& p: _rawPositions) {
    update(0, p, p0);
    update(1, p, p1);
  }
}

bool GLPointCloud::pointSelected(const QVector3D& point, const QRectF& selection, const QRectF& viewport)
{
  // Must cull z < znear; not visible therefore not part of the selection.
  auto wpoint = toWindow(point, viewport);
  return selection.contains(QPointF(wpoint.x(), wpoint.y())) && wpoint.z() >= 0.1f; // XXX: hard-coded znear; see GLRenderer::updateWorldMatrix
}

// Not quite correct name as it also accounts for z and chooses the one nearest to the viewer.
float GLPointCloud::screenDistance(const QVector3D& point, const QPointF& target, const QRectF& viewport)
{
  auto wpoint = toWindow(point, viewport);
  if (wpoint.z() < 0.1)                 // XXX: hard-coded znear; force large distance
    wpoint.setZ(INF_COORD);
  return QVector3D(target.x(), target.y(), 0).distanceToPoint(wpoint);
}

// NOTE: _cameraMatrix is static and is actually the MVP matrix used for rendering
// NOTE: viewport is defined WRT the window, but mouse coordinates have (0,0) at widget
// origin, which is what we need. Therefore no need to add viewport.x/y when computing
// the window coordinate.
// Return: x,y are window coordinates, z is in NDC
QVector3D GLPointCloud::toWindow(const QVector3D& point, const QRectF& viewport)
{
  auto projected = _cameraMatrix.map(QVector4D(point[0], point[1], point[2], 1));
  auto ndc = QVector3D(projected) / projected.w();
  return QVector3D(
    viewport.width()/2*(ndc[0]+1),
    viewport.height()/2*(-ndc[1]+1),  // invert y [ndc is opposite way of win]
    ndc.z());
}

void GLPointCloud::draw()
{
  _program.bind();

  const bool depthTestEnabled = glIsEnabled(GL_DEPTH_TEST); 
  glDisable(GL_DEPTH_TEST);
  
  _vertexArrayObject.bind();
  glPointSize(_isSelection ? 6.0f : 1.0f);
  glDrawArrays(GL_POINTS, 0, (GLint)_rawPositions.size());
  _vertexArrayObject.release();
  
  if (depthTestEnabled)
    glEnable(GL_DEPTH_TEST);
  
  _program.release();
}

} // namespace
