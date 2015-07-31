#include "GLRenderer.hpp"
#include "GLView.hpp"
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
    updateWorldMatrix();
}

GLRenderer::~GLRenderer()
{
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
}

void GLRenderer::updateWorldMatrix()
{
    // projection
    QMatrix4x4 projMat;
    projMat.perspective(45.0f, _viewportSize.width() / (float)_viewportSize.height(), 0.1f, 100.0f);
    // world
    QMatrix4x4 worldMat;
    worldMat = projMat * _cameraMat * _gizmo->modelMatrix();
    // update shaders
    _coloredShader->setWorldMatrix(worldMat);
    _plainColorShader->setWorldMatrix(worldMat);
}

} // namespace
