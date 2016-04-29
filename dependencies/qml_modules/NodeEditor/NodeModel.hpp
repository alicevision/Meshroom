#pragma once

#include <QAbstractListModel>
#include "Node.hpp"

namespace nodeeditor
{

class NodeModel : public QAbstractListModel
{
    Q_OBJECT
    Q_PROPERTY(int count READ rowCount NOTIFY countChanged)

public:
    enum NodeRoles
    {
        NameRole = Qt::UserRole + 1,
        AttributesRole,
        ModelDataRole
    };

public:
    NodeModel(QObject* parent = 0);
    NodeModel(QObject* parent, const NodeModel& obj);
    void addNode(Node* node);
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    Node* get(const QString& name);

public:
    Q_SLOT void addNode(const QString& name);
    Q_SLOT QVariantMap get(int row) const;
    Q_SIGNAL void countChanged(int c);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Node*> _nodes;
};

} // namespace
