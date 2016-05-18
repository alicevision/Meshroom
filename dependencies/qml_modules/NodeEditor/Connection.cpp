#include "Connection.hpp"
#include <QJsonObject>

namespace nodeeditor
{

void Connection::setSourceID(const int& sourceID)
{
    if(_sourceID == sourceID)
        return;
    _sourceID = sourceID;
    Q_EMIT sourceIDChanged();
}

void Connection::setTargetID(const int& targetID)
{
    if(_targetID == targetID)
        return;
    _targetID = targetID;
    Q_EMIT targetIDChanged();
}

void Connection::setSlotID(const int& slotID)
{
    if(_slotID == slotID)
        return;
    _slotID = slotID;
    Q_EMIT slotIDChanged();
}

QJsonObject Connection::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("sourceID", _sourceID);
    obj.insert("targetID", _targetID);
    obj.insert("slotID", _slotID);
    return obj;
}

void Connection::deserializeFromJSON(const QJsonObject& obj)
{
    _sourceID = obj.value("sourceID").toInt();
    _targetID = obj.value("targetID").toInt();
    _slotID = obj.value("slotID").toInt();
}

} // namespace
