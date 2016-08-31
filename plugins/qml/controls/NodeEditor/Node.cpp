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
    _type = obj.value("type").toString();
    _x = obj.value("x").toInt();
    _y = obj.value("y").toInt();
    for(auto o : obj.value("inputs").toArray())
        _inputs->addAttribute(o.toObject());
    for(auto o : obj.value("outputs").toArray())
        _outputs->addAttribute(o.toObject());
}

} // namespace
