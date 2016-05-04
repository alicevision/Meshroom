#include "Graph.hpp"
#include <QJsonObject>

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
    Q_EMIT nodeAdded("imageListing");
    Q_EMIT nodeAdded("featureExtraction");
    Q_EMIT nodeAdded("featureMatching");
    Q_EMIT nodeAdded("structureFromMotion");
    Q_EMIT nodeAdded("exportPLY");
    Q_EMIT connectionAdded(0, 1, 0);
    Q_EMIT connectionAdded(1, 2, 0);
    Q_EMIT connectionAdded(2, 3, 0);
    Q_EMIT connectionAdded(3, 4, 0);
}

void Graph::serializeToJSON(QJsonObject* obj) const
{
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
