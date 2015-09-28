#include "ResourceModel.hpp"
#include <QQmlEngine>
#include <QDebug>

namespace mockup
{

ResourceModel::ResourceModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int ResourceModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _resources.count();
}

QVariant ResourceModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _resources.count())
        return QVariant();
    Resource* resource = _resources[index.row()];
    switch(role)
    {
        case UrlRole:
            return resource->url();
        case NameRole:
            return resource->name();
        case ModelDataRole:
            return QVariant::fromValue(resource);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> ResourceModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[UrlRole] = "url";
    roles[NameRole] = "name";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void ResourceModel::addResource(Resource* resource)
{
    for(size_t i = 0; i < _resources.count(); ++i)
    {
        if(_resources[i]->url() == resource->url())
            return;
    }

    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(resource, QQmlEngine::CppOwnership);
    resource->setParent(this);

    _resources << resource;
    endInsertRows();
    emit countChanged(rowCount());
}

void ResourceModel::addResource(const QUrl& url)
{
    Resource* r = new Resource(url);
    addResource(r);
}

void ResourceModel::removeResource(Resource* resource)
{
    int id = _resources.indexOf(resource);
    if(id < 0)
        return;
    beginRemoveRows(QModelIndex(), id, id);
    _resources.removeAt(id);
    delete resource;
    endRemoveRows();
    emit countChanged(rowCount());
}

} // namespace
