#pragma once

#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>
#include "GLDrawable.hpp"

// GLCamera Gizmo
// draw a simple camera

namespace meshroom
{

class GLCamera : public GLDrawable
{

public:
    GLCamera();
    ~GLCamera() = default;

public:
    void draw() override;
    void setProjectionMatrix(const QMatrix4x4& mat) { _projectionMatrix = mat; }
    void setImagePlane(const std::string& filename) { _imagePlane = filename; }
    const std::string& getImagePlane() const { return _imagePlane; }

private:
    QOpenGLVertexArrayObject _vao;
    QMatrix4x4 _projectionMatrix;
    std::string _imagePlane;
    static QVector<float> _cameraMesh;
    static QVector<float> _cameraMeshColors;
};

} // namespace
