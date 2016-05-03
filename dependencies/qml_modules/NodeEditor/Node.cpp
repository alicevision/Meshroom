#include "Node.hpp"
#include <QJsonObject>

namespace nodeeditor
{

Node::Node(const QString& name)
    : _name(name)
    , _inputs(new AttributeModel(this))
    , _outputs(new AttributeModel(this))
{
    Attribute* out = new Attribute();
    out->setName("output");
    _outputs->addAttribute(out);
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
}

} // namespace
