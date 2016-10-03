#pragma once

#include <QObject>
#include <QJsonObject>
#include "NodeCollection.hpp"
#include "EdgeCollection.hpp"

namespace nodeeditor
{

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(NodeCollection* nodes READ nodes CONSTANT)
    Q_PROPERTY(EdgeCollection* edges READ edges CONSTANT)

public:
    Graph(QObject* = nullptr);
    ~Graph() = default;

public:
    NodeCollection* nodes() const { return _nodes; }
    EdgeCollection* edges() const { return _edges; }

public:
    Q_SLOT void clear();
    Q_SLOT bool addNode(const QJsonObject&) const;
    Q_SLOT bool addEdge(const QJsonObject&) const;
    Q_SLOT bool removeNode(const QJsonObject&) const;
    Q_SLOT bool removeEdge(const QJsonObject&) const;
    Q_SLOT void clearNodeStatuses() const;
    Q_SLOT void setNodeStatus(const QString&, const QString&) const;
    Q_SLOT void setNodeAttribute(const QString&, const QString&, const QVariant&) const;

public:
    Q_SLOT QJsonObject serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonObject&);

private:
    NodeCollection* _nodes = new NodeCollection(this);
    EdgeCollection* _edges = new EdgeCollection(this);
};

} // namespace
