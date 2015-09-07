#include "CameraModel.hpp"
#include <QFileInfo>

namespace mockup
{

CameraModel::CameraModel(const QUrl& url, QObject* parent)
    : QObject(parent)
    , _lookAtRadius(0)
{
    setUrl(url);
    // Init camera position
    QVector3D eye = QVector3D(0, 5, -10);
    QVector3D up = QVector3D(0, 1, 0);
    QVector3D center = QVector3D(0, 0, 0);
    _viewMatrix.lookAt(eye, center, up);

    // Position of the target to look at on the z axis:
    _lookAtRadius = (eye - center).length();

    emit viewMatrixChanged();
}

QString CameraModel::name() const
{
    return _name;
}

void CameraModel::setName(const QString& name)
{
    if(name != _name)
    {
        _name = name;
        emit nameChanged();
    }
}

QUrl CameraModel::url() const
{
    return _url;
}

void CameraModel::setUrl(const QUrl& url)
{
    if(url != _url)
    {
        if(!url.isValid())
            return;
        QFileInfo fileInfo(url.toLocalFile());
        setName(fileInfo.completeBaseName());
        _url = url;
        emit urlChanged();
    }
}
void CameraModel::setViewMatrix(const QMatrix4x4& mat)
{

    if(_viewMatrix != mat)
    {
        _viewMatrix = mat;
        emit viewMatrixChanged();
    }
}

// Returns the "look at" point on the optical axis (-z)
// It is used as a center of rotation while manipulating
QVector3D CameraModel::lookAt() const
{
    return std::move(_viewMatrix.inverted() * QVector3D(0.0, 0.0, -_lookAtRadius));
}

const QMatrix4x4& CameraModel::viewMatrix() const
{
    return _viewMatrix;
}

} // namespace
