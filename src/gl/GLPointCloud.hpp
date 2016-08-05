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
    GLPointCloud(bool isSelection = false);
    ~GLPointCloud() = default;

    void draw() override;
    void setRawPositions(const void* points, size_t npoints);
    void setRawColors(const void* points, size_t npoints);
    void selectPoints(std::vector<QVector3D>& selectedPositions, const QRectF& selection, const QRectF& viewport);
    void selectPoints(std::vector<QVector3D>& selectedPositions, const QPointF& p0, const QPointF& p1, const QRectF& viewport);

private:
    static const float INF_COORD;
    
    const bool _isSelection;
    QOpenGLVertexArrayObject _vertexArrayObject;
    QOpenGLBuffer _pointPositions;
    QOpenGLBuffer _pointColors;
    std::vector<QVector3D> _rawPositions;
    
    bool pointSelected(const QVector3D& point, const QRectF& selection, const QRectF& viewport);
    inline float screenDistance(const QVector3D& point, const QPointF& target, const QRectF& viewport);
    inline QVector3D toWindow(const QVector3D& point, const QRectF& viewport);
};

} // namespace
