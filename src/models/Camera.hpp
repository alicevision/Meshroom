#pragma once

#include <QObject>
#include <QMatrix4x4>

namespace meshroom
{

class Camera : public QObject
{
    Q_OBJECT

public:
    Camera();

public:
    Q_SLOT const QMatrix4x4& viewMatrix() const { return _viewMatrix; }
    Q_SLOT const float& lookAtRadius() { return _lookAtRadius; }
    Q_SLOT void setViewMatrix(const QMatrix4x4& mat);
    Q_SLOT void setLookAtRadius(float radius);

public:
    QVector3D lookAt() const;

private:
    QMatrix4x4 _viewMatrix;
    float _lookAtRadius;
};

} // namespace
