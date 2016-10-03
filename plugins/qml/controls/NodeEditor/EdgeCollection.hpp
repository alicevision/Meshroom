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
    EdgeCollection(QObject* parent = 0);
    EdgeCollection(const EdgeCollection& obj) = delete;
    EdgeCollection& operator=(EdgeCollection const&) = delete;

public:
    int rowCount(const QModelIndex& parent = QModelIndex()) const override;
    QVariant data(const QModelIndex& index, int role = Qt::DisplayRole) const override;
    bool setData(const QModelIndex& index, const QVariant& value, int role) override;

public:
    Q_SLOT bool add(Edge*);
    Q_SLOT bool remove(Edge*);
    Q_SLOT void removeNodeEdges(Node* node);
    Q_SLOT void clear();
    Q_SLOT int rowIndex(Edge*) const;
    Q_SLOT int rowIndex(const QString&, const QString&, const QString&) const;
    Q_SLOT QVariantMap toVMap(int) const;
    Q_SLOT QJsonArray serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonArray&);
    Q_SIGNAL void countChanged(int);

protected:
    QHash<int, QByteArray> roleNames() const override;

private:
    QList<Edge*> _edges;
};

} // namespace
