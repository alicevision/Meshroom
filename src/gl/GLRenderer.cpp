#include "GLRenderer.hpp"
#include "GLView.hpp"
#include "GLPointCloud.hpp"
#include "models/CameraModel.hpp"
#include <iostream>

namespace mockup
{

GLRenderer::GLRenderer()
{
    _coloredShader = new GLSLColoredShader();
    _plainColorShader = new GLSLPlainColorShader();
    _gizmo = new GLGizmo(_coloredShader->program());
    _grid = new GLGrid(_plainColorShader->program());
    _pointCloud = new GLPointCloud(_plainColorShader->program());
    updateWorldMatrix();
}

GLRenderer::~GLRenderer()
{
    if(_pointCloud)
        delete _pointCloud;
    if(_gizmo)
        delete _gizmo;
    if(_grid)
        delete _grid;
    if(_coloredShader)
        delete _coloredShader;
    if(_plainColorShader)
        delete _plainColorShader;
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
}

void GLRenderer::draw()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    _gizmo->draw();
    _grid->draw();
    if (_pointCloud)
        _pointCloud->draw();
}

void GLRenderer::updateWorldMatrix()
{
    // projection
    QMatrix4x4 projMat;
    projMat.perspective(60.0f, _viewportSize.width() / (float)_viewportSize.height(), 0.1f, 100.0f);
    // world
    QMatrix4x4 worldMat;
    worldMat = projMat * _cameraMat ;
    // update shaders
    _coloredShader->setWorldMatrix(worldMat*_gizmo->modelMatrix());
    _plainColorShader->setWorldMatrix(worldMat);
}

// FIXME: setGizmoPosition should certainly move away from the renderer
// At the moment it is used as a convenience function for testing the camera
// manipulation
void GLRenderer::setGizmoPosition(const QVector3D &pos)
{
    if(_gizmo)
    {
        _gizmo->setPosition(pos);
    }
}
} // namespace
