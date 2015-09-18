#pragma once

#include <QObject>
#include <QMatrix4x4>

namespace mockup
{

class Camera : public QObject
{
    Q_OBJECT

public:
    Camera();

public slots:
    const QMatrix4x4& viewMatrix() const { return _viewMatrix; }
    const float& lookAtRadius() { return _lookAtRadius; }
    void setViewMatrix(const QMatrix4x4& mat);
    void setLookAtRadius(float radius);

public:
    QVector3D lookAt() const;

private:
    QMatrix4x4 _viewMatrix;
    float _lookAtRadius;
};

} // namespace
