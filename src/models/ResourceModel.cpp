#include "ResourceModel.hpp"
#include <QFileInfo>
#include <QDir>

namespace mockup
{

ResourceModel::ResourceModel(const QUrl& url, QObject* parent)
    : QObject(parent)
{
    setUrl(url);
}

QUrl ResourceModel::url() const
{
    return _url;
}

void ResourceModel::setUrl(const QUrl& url)
{
    if(url != _url)
    {
        if(!url.isValid())
            return;
        _url = url;
        QFileInfo fileInfo(url.toLocalFile());
        _isDir = fileInfo.isDir();
        setName(_isDir ? fileInfo.dir().dirName() : fileInfo.fileName());
        emit urlChanged();
    }
}

const QString& ResourceModel::name() const
{
    return _name;
}

void ResourceModel::setName(const QString& name)
{
    if(name != _name)
    {
        _name = name;
        emit nameChanged();
    }
}

bool ResourceModel::isDir() const
{
    return _isDir;
}

// static
bool ResourceModel::isValidUrl(const QUrl& url)
{
    if(!url.isValid())
        return false;
    QFileInfo fileInfo(url.toLocalFile());
    if(fileInfo.isDir())
        return true;
    foreach(QString e, validFileExtensions())
    {
        QString suffix = fileInfo.suffix().toLower();
        if(suffix == e.right(suffix.size()))
            return true;
    }
    return false;
}

} // namespace
