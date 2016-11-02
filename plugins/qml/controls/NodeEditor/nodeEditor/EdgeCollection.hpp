#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "Edge.hpp"

namespace nodeeditor
{

class Node;

class EdgeCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum EdgeRoles
    {
        SourceRole = Qt::UserRole + 1,
        TargetRole,
        PlugRole,
        ModelDataRole
    };
    Q_ENUMS(EdgeRoles)

public:
    EdgeCollection(NodeCollection&, QObject* parent = 0);
    EdgeCollection(const EdgeCollection& obj) = delete;
    EdgeCollection& operator=(EdgeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public:
    Q_SLOT bool add(Edge*);
    Q_SLOT bool remove(Edge*);
    Q_SLOT bool remove(const QJsonObject&);
    Q_SLOT void clear();
    Q_SLOT int rowIndex(Edge*) const;
    Q_SLOT int rowIndex(const QJsonObject&) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Edge*> _edges;
    NodeCollection& _nodes;
};

inline EdgeCollection::EdgeCollection(NodeCollection& nodes, QObject* parent)
    : QAbstractListModel(parent)
    , _nodes(nodes)
{
}

inline int EdgeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _edges.count();
}

inline QVariant EdgeCollection::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _edges.count())
        return QVariant();
    Edge* edge = _edges[index.row()];
    switch(role)
    {
        case SourceRole:
            return edge->source();
        case TargetRole:
            return edge->target();
        case PlugRole:
            return edge->plug();
        case ModelDataRole:
            return QVariant::fromValue(edge);
        default:
            return QVariant();
    }
}

inline bool EdgeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
{
    if(index.row() < 0 || index.row() >= _edges.count())
        return false;
    Edge* edge = _edges[index.row()];
    switch(role)
    {
        case SourceRole:
            edge->setSource(value.toString());
            break;
        case TargetRole:
            edge->setTarget(value.toString());
            break;
        case PlugRole:
            edge->setPlug(value.toString());
            break;
        default:
            return false;
    }
    Q_EMIT dataChanged(index, index);
    return true;
}

inline bool EdgeCollection::add(Edge* edge)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(edge, QQmlEngine::CppOwnership);
    edge->setParent(parent());

    edge->sourceAttribute()->addConnection(edge->targetAttribute());
    edge->targetAttribute()->addConnection(edge->sourceAttribute());

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _edges << edge;
    endInsertRows();

    // handle model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]()
    {
        Q_EMIT dataChanged(id, id);
    };
    connect(edge, &Edge::sourceChanged, this, callback);
    connect(edge, &Edge::targetChanged, this, callback);
    connect(edge, &Edge::plugChanged, this, callback);

    Q_EMIT countChanged(rowCount());
    return true;
}

inline bool EdgeCollection::remove(Edge* edge)
{
    int id = rowIndex(edge);
    if(id < 0)
        return false;

    edge->sourceAttribute()->removeConnection(edge->targetAttribute());
    edge->targetAttribute()->removeConnection(edge->sourceAttribute());

    beginRemoveRows(QModelIndex(), id, id);
    delete _edges.takeAt(id);
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
    return true;
}

inline bool EdgeCollection::remove(const QJsonObject& o)
{
    int id = rowIndex(o);
    if(id < 0)
        return false;
    return remove(_edges.at(id));
}

inline void EdgeCollection::clear()
{
    while(!_edges.isEmpty())
        remove(_edges.first());
}

inline int EdgeCollection::rowIndex(Edge* edge) const
{
    return _edges.indexOf(edge);
}

inline int EdgeCollection::rowIndex(const QJsonObject& o) const
{
    if(!o.contains("source") || !o.contains("target") || !o.contains("plug"))
        return -1;
    auto validator = [&](Edge* e) -> bool
    {
        return (e->source() == o.value("source").toString() &&
                e->target() == o.value("target").toString() &&
                e->plug() == o.value("plug").toString());
    };
    auto it = std::find_if(_edges.begin(), _edges.end(), validator);
    return (it == _edges.end()) ? -1 : std::distance(_edges.begin(), it);
}

inline QJsonArray EdgeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto c : _edges)
        array.append(c->serializeToJSON());
    return array;
}

inline void EdgeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto c : array)
    {
        Edge* edge = new Edge(_nodes);
        edge->deserializeFromJSON(c.toObject());
        add(edge);
    }
}

inline QHash<int, QByteArray> EdgeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[SourceRole] = "source";
    roles[TargetRole] = "target";
    roles[PlugRole] = "plug";
    roles[ModelDataRole] = "modelData";
    return roles;
}

} // namespace
