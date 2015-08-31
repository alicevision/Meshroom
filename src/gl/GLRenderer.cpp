#include "GLRenderer.hpp"
#include "GLGizmo.hpp"
#include "GLGrid.hpp"
#include "GLPointCloud.hpp"
#include "GLView.hpp"
#include "models/CameraModel.hpp"
#include "io/AlembicImport.hpp"
#include <iostream>

namespace mockup
{

GLRenderer::GLRenderer()
{
    // The shaders have to be created in a valid opengl context
    GLDrawable::setShaders(
            new GLSLPlainColorShader(QVector4D(0.8, 0.8, 0.8, 1.0)),
            new GLSLColoredShader());
    _scene.append(new GLGizmo());
    _scene.append(new GLGrid());
    updateWorldMatrix();
}

GLRenderer::~GLRenderer()
{
    for(auto obj: _scene) delete obj;

    GLDrawable::deleteShaders();
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
    for(auto obj: _scene)
    {
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
    GLDrawable::setWorldMatrix(worldMat);
}

void GLRenderer::addAlembicScene(const QString& cloud)
{
    AlembicImport importer(cloud.toStdString().c_str());
    importer.populate(_scene);
}

} // namespace
