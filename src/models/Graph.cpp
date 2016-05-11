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
    // Q_EMIT nodeAdded("imageListing");
    // Q_EMIT nodeAdded("featureExtraction");
    // Q_EMIT nodeAdded("featureMatching");
    // Q_EMIT nodeAdded("structureFromMotion");
    // Q_EMIT nodeAdded("exportPLY");
    // Q_EMIT connectionAdded(0, 1, 0);
    // Q_EMIT connectionAdded(1, 2, 0);
    // Q_EMIT connectionAdded(2, 3, 0);
    // Q_EMIT connectionAdded(3, 4, 0);
}

void Graph::addNode(const QString& nodeType)
{
    QString nodeName = nodeType.toLower();
    _graph.addNode(nodeType.toStdString(), nodeName.toStdString());
    Q_EMIT nodeAdded(nodeName);
}

void Graph::serializeToJSON(QJsonObject* obj) const
{
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
