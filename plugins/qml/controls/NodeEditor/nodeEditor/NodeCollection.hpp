#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include <QQmlEngine>
#include <QDebug>
#include "Node.hpp"

namespace nodeeditor
{

class NodeCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum NodeRoles
    {
        NameRole = Qt::UserRole + 1,
        TypeRole,
        InputsRole,
        OutputsRole,
        StatusRole,
        PositionRole,
        ModelDataRole
    };
    Q_ENUMS(NodeRoles)

public:
    NodeCollection(QObject* parent = 0);
    NodeCollection(const NodeCollection& obj) = delete;
    NodeCollection& operator=(NodeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public:
    Q_SLOT bool add(Node*);
    Q_SLOT bool remove(Node*);
    Q_SLOT bool remove(const QString&);
    Q_SLOT void clear();
    Q_SLOT int rowIndex(Node*) const;
    Q_SLOT int rowIndex(const QString&) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Node*> _nodes;
};

inline NodeCollection::NodeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

inline int NodeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _nodes.count();
}

inline QVariant NodeCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return QVariant();
    Node* node = _nodes[index.row()];
    switch(role)
    {
        case NameRole:
            return node->name();
        case TypeRole:
            return node->type();
        case InputsRole:
            return QVariant::fromValue(node->inputs());
        case OutputsRole:
            return QVariant::fromValue(node->outputs());
        case StatusRole:
            return node->status();
        case PositionRole:
            return node->position();
        case ModelDataRole:
            return QVariant::fromValue(node);
        default:
            return QVariant();
    }
}

inline bool NodeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _nodes.count())
        return false;
    Node* node = _nodes[index.row()];
    switch(role)
    {
        case StatusRole:
            node->setStatus((Node::Status)value.toInt());
            break;
        case PositionRole:
            node->setPosition(value.toPoint());
            break;
        default:
            return false;
    }
    Q_EMIT dataChanged(index, index);
    return true;
}

inline bool NodeCollection::add(Node* node)
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
    connect(node, &Node::positionChanged, this, callback);

    Q_EMIT countChanged(rowCount());
    return true;
}

inline bool NodeCollection::remove(Node* node)
{
    int id = rowIndex(node);
    if(id < 0)
        return false;
    beginRemoveRows(QModelIndex(), id, id);
    delete _nodes.takeAt(id);
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
    return true;
}

inline bool NodeCollection::remove(const QString& nodename)
{
    int id = rowIndex(nodename);
    if(id < 0)
        return false;
    beginRemoveRows(QModelIndex(), id, id);
    delete _nodes.takeAt(id);
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
    return true;
}

inline void NodeCollection::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_nodes.isEmpty())
        delete _nodes.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

inline int NodeCollection::rowIndex(Node* node) const
{
    return _nodes.indexOf(node);
}

inline int NodeCollection::rowIndex(const QString& name) const
{
    auto validator = [&](Node* n) -> bool
    {
        return n->name() == name;
    };
    auto it = std::find_if(_nodes.begin(), _nodes.end(), validator);
    return (it == _nodes.end()) ? -1 : std::distance(_nodes.begin(), it);
}

inline QJsonArray NodeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto n : _nodes)
        array.append(n->serializeToJSON());
    return array;
}

inline void NodeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto n : array)
    {
        Node* node = new Node;
        node->deserializeFromJSON(n.toObject());
        add(node);
    }
}

inline QHash<int, QByteArray> NodeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[NameRole] = "name";
    roles[TypeRole] = "type";
    roles[InputsRole] = "inputs";
    roles[OutputsRole] = "outputs";
    roles[StatusRole] = "status";
    roles[PositionRole] = "position";
    roles[ModelDataRole] = "modelData";
    return roles;
}

} // namespace
