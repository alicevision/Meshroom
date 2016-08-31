#include "Connection.hpp"
#include <QJsonObject>

namespace nodeeditor
{

void Connection::setSource(const QString& source)
{
    if(_source == source)
        return;
    _source = source;
    Q_EMIT sourceChanged();
}

void Connection::setTarget(const QString& target)
{
    if(_target == target)
        return;
    _target = target;
    Q_EMIT targetChanged();
}

void Connection::setSlot(const QString& plug)
{
    if(_plug == plug)
        return;
    _plug = plug;
    Q_EMIT plugChanged();
}

QJsonObject Connection::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("source", _source);
    obj.insert("target", _target);
    obj.insert("plug", _plug);
    return obj;
}

void Connection::deserializeFromJSON(const QJsonObject& obj)
{
    _source = obj.value("source").toString();
    _target = obj.value("target").toString();
    _plug = obj.value("plug").toString();
}

} // namespace
