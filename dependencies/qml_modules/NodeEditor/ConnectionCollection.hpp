#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "Connection.hpp"

namespace nodeeditor
{

class ConnectionCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum ConnectionRoles
    {
        SourceRole = Qt::UserRole + 1,
        TargetRole,
        SlotRole,
        ModelDataRole
    };

public:
    ConnectionCollection(QObject* parent = 0);
    ConnectionCollection(const ConnectionCollection& obj) = delete;
    ConnectionCollection& operator=(ConnectionCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;

public:
    Q_SLOT void addConnection(Connection* connection);
    Q_SLOT void addConnection(const QJsonObject& descriptor);
    Q_SLOT QVariantMap get(int row) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Connection*> _connections;
};

} // namespace
