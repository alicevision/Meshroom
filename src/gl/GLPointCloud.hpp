#pragma once

#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QVector3D>
#include <vector>
#include "GLDrawable.hpp"

namespace meshroom
{

class GLPointCloud : public GLDrawable
{

public:
    GLPointCloud();
    ~GLPointCloud() = default;

    void draw() override;
    void setRawPositions(const void* points, size_t npoints);
    void setRawColors(const void* points, size_t npoints);
    void selectPoints(const QRectF& selection, const QRectF& viewport);

private:
    QOpenGLVertexArrayObject _vertexArrayObject, _selectionVAO;
    QOpenGLBuffer _pointPositions, _selectedPositions;
    QOpenGLBuffer _pointColors;
    GLint _npoints, _nselected;
    std::vector<QVector3D> _rawPositions;
    
    bool pointSelected(const QVector3D& point, const QRectF& selection, const QRectF& viewport);
};

} // namespace
