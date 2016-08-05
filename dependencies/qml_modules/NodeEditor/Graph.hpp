#pragma once

#include <QObject>
#include <QJsonObject>
#include "NodeCollection.hpp"
#include "ConnectionCollection.hpp"

namespace nodeeditor
{

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(NodeCollection* nodes READ nodes CONSTANT)
    Q_PROPERTY(ConnectionCollection* connections READ connections CONSTANT)

public:
    Graph(QObject* = nullptr);
    ~Graph() = default;

public:
    NodeCollection* nodes() const { return _nodes; }
    ConnectionCollection* connections() const { return _connections; }

public:
    Q_SLOT void clear();
    Q_SLOT void addNode(const QJsonObject&) const;
    Q_SLOT void addConnection(const QJsonObject&) const;
    Q_SLOT void clearNodeStatuses() const;
    Q_SLOT void setNodeStatus(const QString&, const QString&) const;
    Q_SLOT void setNodeAttribute(const QString&, const QString&, const QVariant&) const;

public:
    Q_SLOT QJsonObject serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonObject&);

private:
    NodeCollection* _nodes = new NodeCollection(this);
    ConnectionCollection* _connections = new ConnectionCollection(this);
};

} // namespace
