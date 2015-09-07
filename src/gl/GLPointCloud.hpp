#pragma once

#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include "GLDrawable.hpp"

namespace mockup
{

class GLPointCloud : public GLDrawable
{

public:
    GLPointCloud();
    ~GLPointCloud() = default;

    void draw() override;
    void setRawData(const void* points, size_t npoints);

private:
    QOpenGLVertexArrayObject _vertexArrayObject;
    QOpenGLBuffer _pointPositions;
    GLint _npoints;
};

} // namespace
