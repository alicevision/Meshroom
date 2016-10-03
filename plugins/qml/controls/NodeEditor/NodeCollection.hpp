#pragma once

#include <QAbstractListModel>
#include <QJsonArray>
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
        InputsRole,
        OutputsRole,
        StatusRole,
        XRole,
        YRole,
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
    Q_SLOT void clear();
    Q_SLOT int rowIndex(Node*) const;
    Q_SLOT int rowIndex(const QString&) const;
    Q_SLOT QVariantMap toVMap(int) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Node*> _nodes;
};

} // namespace
