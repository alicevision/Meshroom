#include "NodeCollection.hpp"
#include <QQmlEngine>

namespace meshroom
{

NodeCollection::NodeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int NodeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _nodes.count();
}

QVariant NodeCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return QVariant();
    Node* node = _nodes[index.row()];
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

Node* NodeCollection::get(const QString& type)
{
    QListIterator<Node*> it(_nodes);
    while(it.hasNext())
    {
        Node* n = it.next();
        if(n->type() == type)
            return n;
    }
    return nullptr;
}

QHash<int, QByteArray> NodeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[TypeRole] = "type";
    roles[PluginRole] = "plugin";
    roles[VersionRole] = "version";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void NodeCollection::addNode(Node* node)
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
