#include "Edge.hpp"
#include "Graph.hpp"
#include <QDebug>

namespace nodeeditor
{

int Edge::sourceID() const
{
    auto graph = qobject_cast<Graph*>(parent());
    if(!graph)
        return -1;
    auto nodes = graph->nodes();
    if(!nodes)
        return -1;
    return nodes->rowIndex(_source);
}

int Edge::targetID() const
{
    auto graph = qobject_cast<Graph*>(parent());
    if(!graph)
        return -1;
    auto nodes = graph->nodes();
    if(!nodes)
        return -1;
    return nodes->rowIndex(_target);
}

int Edge::plugID() const
{
    auto graph = qobject_cast<Graph*>(parent());
    if(!graph)
        return -1;
    auto nodes = graph->nodes();
    if(!nodes)
        return -1;
    auto modelIndex = nodes->index(targetID());
    auto targetNode = nodes->data(modelIndex, NodeCollection::ModelDataRole).value<Node*>();
    if(!targetNode)
        return -1;
    return targetNode->inputs()->rowIndex(_plug);
}

void Edge::setSource(const QString& source)
{
    if(_source == source)
        return;
    _source = source;
    Q_EMIT sourceChanged();
}

void Edge::setTarget(const QString& target)
{
    if(_target == target)
        return;
    _target = target;
    Q_EMIT targetChanged();
}

void Edge::setPlug(const QString& plug)
{
    if(_plug == plug)
        return;
    _plug = plug;
    Q_EMIT plugChanged();
}

QJsonObject Edge::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("source", _source);
    obj.insert("target", _target);
    obj.insert("plug", _plug);
    return obj;
}

void Edge::deserializeFromJSON(const QJsonObject& obj)
{
    _source = obj.value("source").toString();
    _target = obj.value("target").toString();
    _plug = obj.value("plug").toString();
}

} // namespace
