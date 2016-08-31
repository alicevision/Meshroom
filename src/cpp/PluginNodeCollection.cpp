#include "PluginNodeCollection.hpp"
#include <QQmlEngine>

namespace meshroom
{

PluginNodeCollection::PluginNodeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int PluginNodeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _nodes.count();
}

QVariant PluginNodeCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return QVariant();
    PluginNode* node = _nodes[index.row()];
    switch(role)
    {
        case TypeRole:
            return node->type();
        case PluginRole:
            return node->plugin();
        case VersionRole:
            return node->version();
        case ModelDataRole:
            return QVariant::fromValue(node);
        default:
            return QVariant();
    }
}

PluginNode* PluginNodeCollection::get(const QString& type)
{
    QListIterator<PluginNode*> it(_nodes);
    while(it.hasNext())
    {
        PluginNode* n = it.next();
        if(n->type() == type)
            return n;
    }
    return nullptr;
}

QHash<int, QByteArray> PluginNodeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[TypeRole] = "type";
    roles[PluginRole] = "plugin";
    roles[VersionRole] = "version";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void PluginNodeCollection::add(PluginNode* node)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(node, QQmlEngine::CppOwnership);
    node->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _nodes << node;
    endInsertRows();

    Q_EMIT countChanged(rowCount());
}

} // namespace
