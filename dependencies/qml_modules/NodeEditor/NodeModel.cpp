#include "NodeModel.hpp"
#include <QQmlEngine>

namespace nodeeditor
{

NodeModel::NodeModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

NodeModel::NodeModel(QObject* parent, const NodeModel& obj)
    : QAbstractListModel(parent)
{
    QHash<int, QByteArray> names = roleNames();
    for(size_t i = 0; i < obj.rowCount(); ++i)
    {
        Node* s = obj.get(i)[names[ModelDataRole]].value<Node*>();
        addNode(new Node(*s));
    }
}

void NodeModel::addNode(Node* node)
{
    beginInsertRows(QModelIndex(), rowCount(), rowCount());

    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(node, QQmlEngine::CppOwnership);
    node->setParent(this);

    _nodes << node;
    endInsertRows();
    Q_EMIT countChanged(rowCount());
}

int NodeModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _nodes.count();
}

QVariant NodeModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return QVariant();
    Node* node = _nodes[index.row()];
    switch(role)
    {
        case NameRole:
            return node->name();
        case AttributesRole:
            return QVariant::fromValue(node->attributes());
        case ModelDataRole:
            return QVariant::fromValue(node);
        default:
            return QVariant();
    }
}

Node* NodeModel::get(const QString& name)
{
    QListIterator<Node*> it(_nodes);
    while(it.hasNext())
    {
        Node* s = it.next();
        if(s->name() == name)
            return s;
    }
    return nullptr;
}

QHash<int, QByteArray> NodeModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[AttributesRole] = "attributes";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void NodeModel::addNode(const QString& name)
{
    Node* n = new Node(name);
    addNode(n);
}

QVariantMap NodeModel::get(int row) const
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
