#include "EdgeCollection.hpp"
#include <QQmlEngine>
#include <QJsonObject>
#include <QDebug>

namespace nodeeditor
{

EdgeCollection::EdgeCollection(QObject* parent)
    : QAbstractListModel(parent)
{
}

int EdgeCollection::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _edges.count();
}

QVariant EdgeCollection::data(const QModelIndex& index, int role) const
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

bool EdgeCollection::setData(const QModelIndex& index, const QVariant& value, int role)
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

bool EdgeCollection::add(Edge* edge)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(edge, QQmlEngine::CppOwnership);
    edge->setParent(parent());

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

bool EdgeCollection::remove(Edge* edge)
{
    int id = rowIndex(edge);
    if(id < 0)
        return false;
    beginRemoveRows(QModelIndex(), id, id);
    delete _edges.takeAt(id);
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
    return true;
}

void EdgeCollection::removeNodeEdges(Node* node)
{
    QList<Edge*> edges = _edges; // cpy!
    for(auto e : _edges)
    {
        if(e->source() == node->name() || e->target() == node->name())
            remove(e);
    }
}

void EdgeCollection::clear()
{
    beginRemoveRows(QModelIndex(), 0, rowCount() - 1);
    while(!_edges.isEmpty())
        delete _edges.takeFirst();
    endRemoveRows();
    Q_EMIT countChanged(rowCount());
}

int EdgeCollection::rowIndex(Edge* edge) const
{
    return _edges.indexOf(edge);
}

int EdgeCollection::rowIndex(const QString& src, const QString& target, const QString& plug) const
{
    int id = 0;
    for(auto e : _edges)
    {
        if(e->source() == src && e->target() == target && e->plug() == plug)
            return id;
        ++id;
    }
    return -1;
}

QVariantMap EdgeCollection::toVMap(int row) const
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

QJsonArray EdgeCollection::serializeToJSON() const
{
    QJsonArray array;
    for(auto c : _edges)
        array.append(c->serializeToJSON());
    return array;
}

void EdgeCollection::deserializeFromJSON(const QJsonArray& array)
{
    for(auto c : array)
    {
        Edge* edge = new Edge;
        edge->deserializeFromJSON(c.toObject());
        add(edge);
    }
}

QHash<int, QByteArray> EdgeCollection::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[SourceRole] = "source";
    roles[TargetRole] = "target";
    roles[PlugRole] = "plug";
    roles[ModelDataRole] = "modelData";
    return roles;
}

} // namespace
