#pragma once

#include <QObject>
#include "NodeCollection.hpp"
#include "EdgeCollection.hpp"

namespace nodeeditor
{

class AbstractGraph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(NodeCollection* nodes MEMBER _nodes CONSTANT)
    Q_PROPERTY(EdgeCollection* edges MEMBER _edges CONSTANT)

public:
    AbstractGraph(QObject* parent = nullptr);
    virtual ~AbstractGraph() = default;

protected:
    virtual Q_INVOKABLE void clear() = 0;
    virtual Q_INVOKABLE bool addNode(const QJsonObject&) = 0;
    virtual Q_INVOKABLE bool addEdge(const QJsonObject&) = 0;
    virtual Q_INVOKABLE bool removeNode(const QJsonObject&) = 0;
    virtual Q_INVOKABLE bool removeEdge(const QJsonObject&) = 0;
    virtual Q_INVOKABLE bool setAttribute(const QJsonObject&) = 0;

protected:
    virtual Q_INVOKABLE QJsonObject serializeToJSON() const = 0;
    virtual Q_INVOKABLE void deserializeFromJSON(const QJsonObject&) = 0;

protected:
    NodeCollection* _nodes = new NodeCollection(this);
    EdgeCollection* _edges = new EdgeCollection(this);
};

inline AbstractGraph::AbstractGraph(QObject* parent)
    : QObject(parent)
{
}

} // namespace
