#pragma once

#include <QObject>
#include <Graph.hpp>

namespace meshroom
{

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)

public:
    Graph(QObject* parent);

public:
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT void setName(const QString&);
    Q_SLOT void reload();
    Q_SLOT void addNode(const QString&, const QJsonObject&);

public:
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void nodeAdded(const QString& name, const QJsonObject& descriptor);
    Q_SIGNAL void connectionAdded(int source, int target, int slot);

private:
    void serializeToJSON(QJsonObject*) const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QString _name = "graph1";
    dg::Graph _graph;
};

} // namespace
