#include "Node.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>

namespace nodeeditor
{

Node::Node()
    : _name("unknown")
    , _inputs(new AttributeModel(this))
    , _outputs(new AttributeModel(this))
{
}

Node::Node(const QString& name)
    : _name(name)
    , _inputs(new AttributeModel(this))
    , _outputs(new AttributeModel(this))
{
}

Node::Node(const Node& obj)
    : _name(obj.name())
    , _inputs(new AttributeModel(*(obj.inputs())))
    , _outputs(new AttributeModel(*(obj.outputs())))
{
}

void Node::serializeToJSON(QJsonObject* obj) const
{
}

void Node::deserializeFromJSON(const QJsonObject& obj)
{
    _name = obj.value("name").toString();
    for(auto o : obj.value("inputs").toArray())
        _inputs->addAttribute(o.toObject());
    for(auto o : obj.value("outputs").toArray())
        _outputs->addAttribute(o.toObject());
}

} // namespace
