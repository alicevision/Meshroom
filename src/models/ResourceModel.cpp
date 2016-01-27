#include "ResourceModel.hpp"
#include <QQmlEngine>
#include <QDebug>

namespace meshroom
{

ResourceModel::ResourceModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

ResourceModel::ResourceModel(const ResourceModel& obj)
    : QAbstractListModel(obj.parent())
{
    QHash<int, QByteArray> names = roleNames();
    for(size_t i = 0; i < obj.rowCount(); ++i)
    {
        Resource* r = obj.get(i)[names[ModelDataRole]].value<Resource*>();
        addResource(new Resource(*r));
    }
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

QVariantMap ResourceModel::get(int row) const
{
    QHash<int, QByteArray> names = roleNames();
    QHashIterator<int, QByteArray> i(names);
    QVariantMap result;
    while(i.hasNext())
    {
        i.next();
        QModelIndex idx = index(row, 0);
        QVariant data = idx.data(i.key());
        result[i.value()] = data;
    }
    return result;
}

} // namespace
