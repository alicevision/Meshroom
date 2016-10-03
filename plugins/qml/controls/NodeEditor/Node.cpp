#include "Node.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QDebug>

namespace nodeeditor
{

void Node::setStatus(Status status)
{
    if(_status == status)
        return;
    _status = status;
    Q_EMIT statusChanged();
}

void Node::setX(int x)
{
    if(_x == x)
        return;
    _x = x;
    Q_EMIT xChanged();
}

void Node::setY(int y)
{
    if(_y == y)
        return;
    _y = y;
    Q_EMIT yChanged();
}

QJsonObject Node::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("name", _name);
    obj.insert("type", _type);
    obj.insert("x", _x);
    obj.insert("y", _y);
    obj.insert("inputs", _inputs->serializeToJSON());
    obj.insert("outputs", _outputs->serializeToJSON());
    return obj;
}

void Node::deserializeFromJSON(const QJsonObject& obj)
{
    if(obj.contains("name"))
        _name = obj.value("name").toString();
    if(obj.contains("type"))
        _type = obj.value("type").toString();
    if(obj.contains("x"))
        _x = obj.value("x").toInt();
    if(obj.contains("y"))
        _y = obj.value("y").toInt();
    for(auto o : obj.value("inputs").toArray())
    {
        Attribute* a = new Attribute;
        a->deserializeFromJSON(o.toObject());
        _inputs->add(a);
    }
    for(auto o : obj.value("outputs").toArray())
    {
        Attribute* a = new Attribute;
        a->deserializeFromJSON(o.toObject());
        _outputs->add(a);
    }
}

} // namespace
