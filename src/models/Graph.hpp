#pragma once

#include <QObject>
#include <Graph.hpp>

namespace meshroom
{

class Application; // forward declaration

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)

public:
    Graph(QObject* parent);

public:
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT void setName(const QString&);
    Q_SLOT void addNode(const QJsonObject&);
    Q_SLOT void addConnection(const QJsonObject&);

public:
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void nodeAdded(const QJsonObject& descriptor);
    Q_SIGNAL void connectionAdded(const QJsonObject& descriptor);

    Q_SIGNAL void descriptionRequested() const;
    Q_SIGNAL void descriptionReceived(const QJsonArray&, const QJsonArray&);

public:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QString _name = "graph1";
    dg::Graph _graph;
};

} // namespace
