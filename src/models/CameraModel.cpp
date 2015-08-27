#include "CameraModel.hpp"
#include <QFileInfo>

namespace mockup
{

CameraModel::CameraModel(const QUrl& url, QObject* parent)
    : QObject(parent)
{
    setUrl(url);
    // Init camera position
    QVector3D eye = QVector3D(0, 0, -10);
    QVector3D center = QVector3D(0, 0, 0);
    QVector3D up = QVector3D(0, 1, 0);
    _viewMatrix.lookAt(eye, center, up);
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
void CameraModel::setViewMatrix(const QMatrix4x4 &mat)
{
    
    if(_viewMatrix!=mat) 
    {
        _viewMatrix=mat;
        emit viewMatrixChanged();
    }
}
//const QVector3D& CameraModel::eye() const
//{
//    return _eye;
//}
//
//void CameraModel::setEye(const QVector3D& eye)
//{
//    if(eye != _eye)
//    {
//        _eye = eye;
//        emit eyeChanged();
//    }
//}
//
//const QVector3D& CameraModel::center() const
//{
//    return _center;
//}
//
//void CameraModel::setCenter(const QVector3D& center)
//{
//    if(center != _center)
//    {
//        _center = center;
//        emit centerChanged();
//    }
//}
//
//const QVector3D& CameraModel::up() const
//{
//    return _up;
//}
//
//void CameraModel::setUp(const QVector3D& up)
//{
//    if(up != _up)
//    {
//        _up = up;
//        emit upChanged();
//    }
//}

const QMatrix4x4 &CameraModel::viewMatrix() const
{
    return _viewMatrix;
}


} // namespace
