#include "ConnectionModel.hpp"
#include <QQmlEngine>

namespace nodeeditor
{

ConnectionModel::ConnectionModel(QObject* parent)
    : QAbstractListModel(parent)
{
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
    connect(connection, &Connection::sourceIDChanged, this, callback);
    connect(connection, &Connection::targetIDChanged, this, callback);
    connect(connection, &Connection::slotIDChanged, this, callback);

    Q_EMIT countChanged(rowCount());
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
        case SourceIDRole:
            return connection->sourceID();
        case TargetIDRole:
            return connection->targetID();
        case SlotIDRole:
            return connection->slotID();
        case ModelDataRole:
            return QVariant::fromValue(connection);
        default:
            return QVariant();
    }
}

QHash<int, QByteArray> ConnectionModel::roleNames() const
{
    QHash<int, QByteArray> roles;
    roles[SourceIDRole] = "sourceID";
    roles[TargetIDRole] = "targetID";
    roles[SlotIDRole] = "slotID";
    roles[ModelDataRole] = "modelData";
    return roles;
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

} // namespace
