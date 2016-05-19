#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
#include "Node.hpp"

namespace meshroom
{

class NodeCollection : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum NodeRoles
    {
        TypeRole = Qt::UserRole + 1,
        PluginRole,
        VersionRole,
        ModelDataRole
    };

public:
    NodeCollection(QObject* parent = 0);
    NodeCollection(const NodeCollection& obj) = delete;
    NodeCollection& operator=(NodeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex&, int role = Qt::DisplayRole) const override;
    Node* get(const QString& type);

public:
    Q_SLOT void addNode(Node*);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Node*> _nodes;
};

} // namespace
