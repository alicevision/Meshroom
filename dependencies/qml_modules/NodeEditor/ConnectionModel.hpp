#pragma once

#include <QAbstractListModel>
#include "Connection.hpp"

namespace nodeeditor
{

class ConnectionModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum ConnectionRoles
    {
        SourceIDRole = Qt::UserRole + 1,
        TargetIDRole,
        SlotIDRole,
        ModelDataRole
    };

public:
    ConnectionModel(QObject* parent = 0);
    void addConnection(Connection* connection);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;

public:
    Q_SLOT QVariantMap get(int row) const;
    Q_SIGNAL void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Connection*> _connections;
};

} // namespace
