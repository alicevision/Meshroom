#include "Graph.hpp"
#include <QDebug>


namespace nodeeditor
{

Graph::Graph(QObject* parent)
    : QObject(parent)
{
}

void Graph::clear() const
{
}

void Graph::addNode(const QJsonObject& descriptor) const
{
    _nodes->addNode(descriptor);
}

void Graph::addConnection(const QJsonObject& descriptor) const
{
    _connections->addConnection(descriptor);
}

void Graph::clearNodeStatuses() const
{
    for(size_t i = 0; i < _nodes->rowCount(); ++i)
    {
        QModelIndex id = _nodes->index(i, 0);
        _nodes->setData(id, Node::READY, NodeCollection::StatusRole);
    }
}

void Graph::updateNodeStatus(const QString& nodeName, const QString& status) const
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
    Node* node = _nodes->get(nodeName);
    if(!node)
        return;
    node->setStatus(toEnum(status));
}

QJsonObject Graph::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("nodes", _nodes->serializeToJSON());
    obj.insert("connections", _connections->serializeToJSON());
    return obj;
}

void Graph::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
