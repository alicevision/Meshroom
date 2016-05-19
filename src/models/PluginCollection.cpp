#include "PluginCollection.hpp"
#include <QQmlEngine>

namespace meshroom
{

PluginCollection::PluginCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int PluginCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _plugins.count();
}

QVariant PluginCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _plugins.count())
        return QVariant();
    Plugin* plugin = _plugins[index.row()];
    switch(role)
    {
        case NameRole:
            return plugin->name();
        case NodeTypesRole:
            return plugin->nodeTypes();
        case VersionRole:
            return plugin->version();
        case ModelDataRole:
            return QVariant::fromValue(plugin);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> PluginCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[NodeTypesRole] = "nodeTypes";
    roles[VersionRole] = "version";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void PluginCollection::addPlugin(Plugin* plugin)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(plugin, QQmlEngine::CppOwnership);
    plugin->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _plugins << plugin;
    endInsertRows();

    Q_EMIT countChanged(rowCount());
}

} // namespace
