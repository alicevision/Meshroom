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

} // namespace
