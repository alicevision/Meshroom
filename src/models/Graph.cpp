#include "Graph.hpp"
#include <QJsonObject>
#include <QDebug>

namespace meshroom
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
}

void Graph::setName(const QString& name)
{
    if(_name == name)
        return;
    _name = name;
    Q_EMIT nameChanged();
}

void Graph::reload()
{
}

void Graph::addNode(const QString& nodeType, const QJsonObject& descriptor)
{
    QString nodeName = nodeType.toLower();
    // FIXME ----
    _graph.addNode(nodeType.toStdString(), nodeName.toStdString());
    Q_EMIT nodeAdded(nodeName, descriptor);
    // auto node = plugin->createNode(nodeType, nodeName, _graph);
    // _graph.addNode(node);
}

void Graph::serializeToJSON(QJsonObject* obj) const
{
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
