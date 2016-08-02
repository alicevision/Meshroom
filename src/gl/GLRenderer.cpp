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
    _scene.emplace_back(new GLGizmo());
    _scene.emplace_back(new GLGrid());
    updateWorldMatrix();
}

GLRenderer::~GLRenderer()
{
    GLDrawable::deleteShaders();
    // Background is deleted by GLDrawable::deleteShaders
    _background = nullptr;
}

void GLRenderer::setViewportSize(const QSize& size)
{
    _viewportSize = size;
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
    for(auto& obj : _scene)
    {
        // Sets position and orientation
        obj->uploadShaderMatrix();
        if (obj->visible)
            obj->draw();
    }
}

void GLRenderer::updateWorldMatrix()
{
    // projection
    QMatrix4x4 projMat;
    // TODO: get perspective matrix from current camera
    projMat.perspective(60.0f, _viewportSize.width() / (float)_viewportSize.height(), 0.1f, 100.0f);
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

void GLRenderer::addPointsToSelection(const QRectF& selection, const QRectF& viewport)
{
  for (auto& obj: _scene)
  if (auto p = dynamic_cast<GLPointCloud*>(obj.get()))
    p->selectPoints(_selection, selection, viewport);
}

void GLRenderer::clearSelection()
{
  _selection.clear();
}


} // namespace
