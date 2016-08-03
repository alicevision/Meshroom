#pragma once

#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include "GLDrawable.hpp"

namespace meshroom
{

class GLPointCloud : public GLDrawable
{

public:
    GLPointCloud();
    ~GLPointCloud() = default;

    void draw() override;
    void setRawPositions(const void* points, std::size_t npoints);
    void setRawColors(const void* points, std::size_t npoints);
    void setRawVisibility(const std::vector<std::size_t>& vec_visibility, std::size_t npoints);
    void setVisibilityThreshold(float threshold); 
    inline std::size_t getVisibility() { return _visibilityThreshold; }

private:
    QOpenGLVertexArrayObject _vertexArrayObject;
    QOpenGLBuffer _pointPositions;
    QOpenGLBuffer _pointColors;
    QOpenGLBuffer _pointColorsVisibility;
    std::vector<std::size_t> _pointVisibility;
    GLint _npoints;
    std::size_t _visibilityThreshold;
    std::size_t _maxVisibility;
};

} // namespace
