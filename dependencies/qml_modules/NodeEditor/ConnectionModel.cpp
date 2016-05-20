#include "ConnectionModel.hpp"
#include <QQmlEngine>
#include <QJsonObject>

namespace nodeeditor
{

ConnectionModel::ConnectionModel(QObject* parent)
    : QAbstractListModel(parent)
{
}

int ConnectionModel::rowCount(const QModelIndex& parent) const
{
    Q_UNUSED(parent);
    return _connections.count();
}

QVariant ConnectionModel::data(const QModelIndex& index, int role) const
{
    if(index.row() < 0 || index.row() >= _connections.count())
        return QVariant();
    Connection* connection = _connections[index.row()];
    switch(role)
    {
        case SourceRole:
            return connection->source();
        case TargetRole:
            return connection->target();
        case SlotRole:
            return connection->plug();
        case ModelDataRole:
            return QVariant::fromValue(connection);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> ConnectionModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[SourceRole] = "source";
    roles[TargetRole] = "target";
    roles[SlotRole] = "plug";
    roles[ModelDataRole] = "modelData";
    return roles;
}

void ConnectionModel::addConnection(Connection* connection)
{
    // prevent items to be garbage collected in JS
    QQmlEngine::setObjectOwnership(connection, QQmlEngine::CppOwnership);
    connection->setParent(this);

    // insert the new element
    beginInsertRows(QModelIndex(), rowCount(), rowCount());
    _connections << connection;
    endInsertRows();

    // handle model and contained object synchronization
    QModelIndex id = index(rowCount() - 1, 0);
    auto callback = [id, this]()
    {
        Q_EMIT dataChanged(id, id);
    };
    connect(connection, &Connection::sourceChanged, this, callback);
    connect(connection, &Connection::targetChanged, this, callback);
    connect(connection, &Connection::plugChanged, this, callback);

    Q_EMIT countChanged(rowCount());
}

void ConnectionModel::addConnection(const QJsonObject& descriptor)
{
    Connection* connection = new Connection();
    connection->deserializeFromJSON(descriptor);
    addConnection(connection);
}

QVariantMap ConnectionModel::get(int row) const
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

QJsonArray ConnectionModel::serializeToJSON() const
{
    QJsonArray array;
    for(auto c : _connections)
        array.append(c->serializeToJSON());
    return array;
}

void ConnectionModel::deserializeFromJSON(const QJsonArray& array)
{
    for(auto c : array)
        addConnection(c.toObject());
}

} // namespace
