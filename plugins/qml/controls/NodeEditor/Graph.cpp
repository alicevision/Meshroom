#include "Graph.hpp"
#include <QJSValue>
#include <QJsonDocument>
#include <QDebug>

namespace nodeeditor
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
    setObjectName("nodeeditor.qmlPlugin.editor");
}

void Graph::clear()
{
    _nodes->clear();
    _edges->clear();
}

bool Graph::addNode(const QJsonObject& descriptor) const
{
    Node* node = new Node;
    node->deserializeFromJSON(descriptor);
    return _nodes->add(node);
}

bool Graph::addEdge(const QJsonObject& descriptor) const
{
    Edge* edge = new Edge;
    edge->deserializeFromJSON(descriptor);
    return _edges->add(edge);
}

bool Graph::removeNode(const QJsonObject& descriptor) const
{
    QString nodeName = descriptor.value("name").toString();
    auto modelIndex = _nodes->index(_nodes->rowIndex(nodeName));
    Node* node = _nodes->data(modelIndex, NodeCollection::ModelDataRole).value<Node*>();
    // remove in/out edges
    _edges->removeNodeEdges(node);
    // remove node
    return _nodes->remove(node);
}

bool Graph::removeEdge(const QJsonObject& descriptor) const
{
    QString src = descriptor.value("source").toString();
    QString target = descriptor.value("target").toString();
    QString plug = descriptor.value("plug").toString();
    auto modelIndex = _edges->index(_edges->rowIndex(src, target, plug));
    Edge* edge = _edges->data(modelIndex, EdgeCollection::ModelDataRole).value<Edge*>();
    return _edges->remove(edge);
}

void Graph::clearNodeStatuses() const
{
    for(size_t i = 0; i < _nodes->rowCount(); ++i)
    {
        QModelIndex id = _nodes->index(i, 0);
        _nodes->setData(id, Node::READY, NodeCollection::StatusRole);
    }
}

void Graph::setNodeStatus(const QString& nodeName, const QString& status) const
{
    auto toEnum = [](const QString& status) -> Node::Status
    {
        if(status == "READY")
            return Node::READY;
        else if(status == "WAITING")
            return Node::WAITING;
        else if(status == "RUNNING")
            return Node::RUNNING;
        else if(status == "ERROR")
            return Node::ERROR;
        else if(status == "DONE")
            return Node::DONE;
        qWarning() << "unknown node status" << status;
        return Node::READY;
    };
    auto modelIndex = _nodes->index(_nodes->rowIndex(nodeName));
    _nodes->setData(modelIndex, toEnum(status), NodeCollection::StatusRole);
}

void Graph::setNodeAttribute(const QString& nodeName, const QString& plugName,
                             const QVariant& value) const
{
    auto modelIndex = _nodes->index(_nodes->rowIndex(nodeName));
    auto node = _nodes->data(modelIndex, NodeCollection::ModelDataRole).value<Node*>();
    if(!node)
        return;

    auto getAttr = [&](AttributeCollection* collection) -> Attribute*
    {
        int id = collection->rowIndex(plugName);
        if(id < 0)
            return nullptr;
        auto modelIndex = collection->index(id);
        return collection->data(modelIndex, AttributeCollection::ModelDataRole).value<Attribute*>();
    };

    Attribute* att = getAttr(node->inputs());
    if(!att)
    {
        att = getAttr(node->outputs());
        if(!att)
            return;
    }
    att->setValue(value);
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("nodes", _nodes->serializeToJSON());
    obj.insert("edges", _edges->serializeToJSON());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
