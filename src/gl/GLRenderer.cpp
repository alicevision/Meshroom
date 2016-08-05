#include "GLRenderer.hpp"
#include "GLGizmo.hpp"
#include "GLGrid.hpp"
#include "GLPointCloud.hpp"
#include "GLView.hpp"
#include "GLCamera.hpp"
#include "io/AlembicImport.hpp"
#include <QFileInfo>

namespace meshroom
{

GLRenderer::GLRenderer()
    : _background(nullptr)
{
    // The shaders have to be created in a valid opengl context
    _background = new GLSLBackgroundShader();
    GLDrawable::setShaders(
        new GLSLPlainColorShader(QVector4D(0.6, 0.6, 0.6, 1.0)), new GLSLColoredShader(),
        _background); // NOTE : the background shader is handled like the other shaders
    
    // Must be initialized after shaders.
    _scene.emplace_back(new GLGizmo());
    _scene.emplace_back(new GLGrid());
    _selectionPC.reset(new GLPointCloud(true));
    _aligner.reset(new GLAligner());
    updateWorldMatrix();
}

GLRenderer::~GLRenderer()
{
    GLDrawable::deleteShaders();
    // Background is deleted by GLDrawable::deleteShaders
    _background = nullptr;
}

void GLRenderer::setViewport(const QRect& viewport)
{
    _viewport = viewport;
    updateWorldMatrix();
}

void GLRenderer::setClearColor(const QColor& color)
{
    glClearColor(color.redF(), color.greenF(), color.blueF(), color.alphaF());
}

void GLRenderer::setCameraMatrix(const QMatrix4x4& cameraMat)
{
    _cameraMat = cameraMat;
    updateWorldMatrix();
}

void GLRenderer::setShowCameras(bool v)
{
    for(auto& obj : _scene)
    {
        if (dynamic_cast<GLCamera*>(obj.get()) != NULL)
            obj->visible = v;
    }
}

void GLRenderer::setShowGrid(bool v)
{
    for(auto& obj : _scene)
    {
        if (dynamic_cast<GLGrid*>(obj.get()) != NULL)
            obj->visible = v;
    }
}

void GLRenderer::draw()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    _background->draw();

    // Draw selection first, so that it's overdrawn with real point cloud points.
    _selectionPC->uploadShaderMatrix();
    _selectionPC->draw();
    
    for(auto& obj : _scene)
    {
        // Sets position and orientation
        obj->uploadShaderMatrix();
        if (obj->visible)
            obj->draw();
    }
    
    // TODO: enable alpha blending
    _aligner->uploadShaderMatrix();
    _aligner->draw();
}

void GLRenderer::updateWorldMatrix()
{
    // projection
    QMatrix4x4 projMat;
    // TODO: get perspective matrix from current camera
    projMat.perspective(60.0f, _viewport.width() / (float)_viewport.height(), 0.1f, 100.0f);
    // world
    QMatrix4x4 worldMat = projMat * _cameraMat;
    // update shaders
    GLDrawable::setCameraMatrix(worldMat);
}

void GLRenderer::addAlembicScene(const QUrl& url)
{
    QFileInfo file(url.toLocalFile());
    if(file.exists() && file.isFile())
    {
#if WITH_ALEMBIC
        AlembicImport importer(url.toLocalFile().toLatin1().data());
        importer.populate(_scene);
#endif
    }
}

void GLRenderer::resetScene()
{
    _scene.clear();
    _scene.emplace_back(new GLGizmo());
    _scene.emplace_back(new GLGrid());
}

void GLRenderer::addPointsToSelection(const QRectF& selection)
{
  for (auto& obj: _scene)
  if (auto p = dynamic_cast<GLPointCloud*>(obj.get()))
    p->selectPoints(_selection, selection, _viewport);
  _selectionPC->setRawPositions(_selection.data(), _selection.size());
}

void GLRenderer::addPointsToSelection(const QPointF& p0, const QPointF& p1)
{
  std::vector<QVector3D> selection;
  for (auto& obj: _scene)
  if (auto p = dynamic_cast<GLPointCloud*>(obj.get()))
    p->selectPoints(selection, p0, p1, _viewport);
  
  _selection.push_back(selection[0]);
  _selection.push_back(selection[1]);
  _selectionPC->setRawPositions(_selection.data(), _selection.size());
}

void GLRenderer::clearSelection()
{
  _selection.clear();
  _selectionPC->setRawPositions(_selection.data(), _selection.size());
}

void GLRenderer::setPlane(const QVector3D& normal, const QVector3D& origin)
{
  _aligner->setPlane(normal, origin);
}

void GLRenderer::clearPlane()
{
  _aligner->clearPlane();
}

void GLRenderer::setDistanceLine(const QPointF& p0, const QPointF& p1)
{
  if (_selection.size() == 2) {
    _selectionPC->setRawPositions(_selection.data(), _selection.size());
    _aligner->setDistanceLine(_selection[0], _selection[1]);
  }
}

void GLRenderer::clearDistanceLine()
{
  _aligner->clearDistanceLine();
}

} // namespace
