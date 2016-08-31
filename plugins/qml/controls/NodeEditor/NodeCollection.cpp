#include "NodeCollection.hpp"
#include <QQmlEngine>
#include <QJsonObject>

namespace nodeeditor
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
        case NameRole:
            return node->name();
        case InputsRole:
            return QVariant::fromValue(node->inputs());
        case OutputsRole:
            return QVariant::fromValue(node->outputs());
        case StatusRole:
            return node->status();
        case XRole:
            return node->x();
        case YRole:
            return node->y();
        case ModelDataRole:
            return QVariant::fromValue(node);
        default:
            return QVariant();
    }
}

bool NodeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return false;
    Node* node = _nodes[index.row()];
    switch(role)
    {
        case StatusRole:
            node->setStatus((Node::Status)value.toInt());
            break;
        case XRole:
            node->setX(value.toInt());
            break;
        case YRole:
            node->setY(value.toInt());
            break;
        default:
            return false;
    }
    Q_EMIT dataChanged(index, index);
    return true;
}

Node* NodeCollection::get(const QString& name)
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

QHash<int, QByteArray> NodeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[InputsRole] = "inputs";
    roles[OutputsRole] = "outputs";
    roles[StatusRole] = "status";
    roles[XRole] = "x";
    roles[YRole] = "y";
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

    // handle model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]()
    {
        Q_EMIT dataChanged(id, id);
    };
    connect(node, &Node::statusChanged, this, callback);
    connect(node, &Node::xChanged, this, callback);
    connect(node, &Node::yChanged, this, callback);

    Q_EMIT countChanged(rowCount());
}

void NodeCollection::addNode(const QJsonObject& descriptor)
{
    Node* node = new Node();
    node->deserializeFromJSON(descriptor);
    addNode(node);
}

void NodeCollection::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_nodes.isEmpty())
        delete _nodes.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

QVariantMap NodeCollection::get(int row) const
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

int NodeCollection::getID(const QString& name) const
{
    int id = 0;
    for(auto n : _nodes)
    {
        if(n->name() == name)
            return id;
        ++id;
    }
    return -1;
}

QJsonArray NodeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto n : _nodes)
        array.append(n->serializeToJSON());
    return array;
}

void NodeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto n : array)
        addNode(n.toObject());
}

} // namespace
