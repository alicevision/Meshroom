#include "CameraModel.hpp"
#include <QFileInfo>

namespace mockup
{

CameraModel::CameraModel(const QUrl& url, QObject* parent)
    : QObject(parent)
{
    setUrl(url);
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

const QVector3D& CameraModel::eye() const
{
    return _eye;
}

void CameraModel::setEye(const QVector3D& eye)
{
    if(eye != _eye)
    {
        _eye = eye;
        emit eyeChanged();
    }
}

const QVector3D& CameraModel::center() const
{
    return _center;
}

void CameraModel::setCenter(const QVector3D& center)
{
    if(center != _center)
    {
        _center = center;
        emit centerChanged();
    }
}

const QVector3D& CameraModel::up() const
{
    return _up;
}

void CameraModel::setUp(const QVector3D& up)
{
    if(up != _up)
    {
        _up = up;
        emit upChanged();
    }
}

QMatrix4x4 CameraModel::viewMatrix() const
{
    QMatrix4x4 viewMat;
    viewMat.lookAt(_eye, _center, _up);
    return viewMat;
}


} // namespace
