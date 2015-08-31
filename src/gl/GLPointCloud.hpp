#pragma once

#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>

namespace mockup
{

class GLPointCloud
{

public:
    GLPointCloud(QOpenGLShaderProgram&, const QString& cloud);
    ~GLPointCloud() = default;

public:
    void draw();
    // template <typename DATA>
    // static GLPointCloud* createFrom(const DATA&);

private:
    QOpenGLVertexArrayObject _vertexArrayObject;
    QOpenGLBuffer _pointPositions;
    GLint _npoints;
    QOpenGLShaderProgram& _program;
};

} // namespace
