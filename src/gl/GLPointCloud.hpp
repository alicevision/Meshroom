#pragma once

#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>

#include "GLDrawable.hpp"

namespace mockup
{

class GLPointCloud : public GLDrawable
{

public:
    GLPointCloud(QOpenGLShaderProgram&, const QString& cloud);
    ~GLPointCloud() = default;

    void draw() override;
    // template <typename DATA>
    // static GLPointCloud* createFrom(const DATA&);

private:
    QOpenGLVertexArrayObject _vertexArrayObject;
    QOpenGLBuffer _pointPositions;
    GLint _npoints;
    QOpenGLShaderProgram& _program;
};

} // namespace
