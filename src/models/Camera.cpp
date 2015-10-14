#include "Camera.hpp"
#include <QFileInfo>

namespace meshroom
{

Camera::Camera()
    : _lookAtRadius(0)
{
    // init camera position
    QVector3D eye = QVector3D(0, 5, 10);
    QVector3D up = QVector3D(0, 1, 0);
    QVector3D center = QVector3D(0, 0, 0);
    QMatrix4x4 viewMatrix;
    viewMatrix.lookAt(eye, center, up);
    setViewMatrix(viewMatrix);
    // position of the target to look at on the z axis
    setLookAtRadius((eye - center).length());
}

void Camera::setViewMatrix(const QMatrix4x4& mat)
{

    if(_viewMatrix == mat)
        return;
    _viewMatrix = mat;
}

void Camera::setLookAtRadius(float radius)
{
    _lookAtRadius = radius > 0.0 ? radius : 0.0;
}

// Returns the "look at" point on the optical axis (-z)
// It is used as a center of rotation while manipulating
QVector3D Camera::lookAt() const
{
    return std::move(_viewMatrix.inverted() * QVector3D(0.0, 0.0, -_lookAtRadius));
}

} // namespace
