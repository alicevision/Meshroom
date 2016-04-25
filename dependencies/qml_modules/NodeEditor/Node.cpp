#include "Node.hpp"
#include <QJsonObject>

namespace nodeeditor
{

Node::Node(const QString& name)
    : _name(name)
    , _attributes(new AttributeModel(this))
{
}

Node::Node(const Node& obj)
    : _name(obj.name())
    , _attributes(new AttributeModel(*(obj.attributes())))
{
}

void Node::serializeToJSON(QJsonObject* nodesObject) const
{
    if(!nodesObject)
        return;
    QJsonObject nodeObject;
    for(size_t i = 0; i < _attributes->rowCount(); i++)
    {
        QModelIndex id = _attributes->index(i, 0);
        Attribute* att = _attributes->data(id, AttributeModel::ModelDataRole).value<Attribute*>();
        att->serializeToJSON(&nodeObject);
    }
    if(!nodeObject.empty())
        nodesObject->insert(_name, nodeObject);
}

void Node::deserializeFromJSON(const QJsonObject& nodesObject)
{
    if(!nodesObject.contains(_name))
        return;
    QJsonObject nodeObject = nodesObject[_name].toObject();
    for(size_t i = 0; i < _attributes->rowCount(); i++)
    {
        QModelIndex id = _attributes->index(i, 0);
        Attribute* att = _attributes->data(id, AttributeModel::ModelDataRole).value<Attribute*>();
        if(!att)
            continue;
        att->deserializeFromJSON(nodeObject);
    }
}

} // namespace
