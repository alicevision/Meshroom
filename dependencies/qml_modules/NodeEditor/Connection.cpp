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

void Connection::serializeToJSON(QJsonObject* obj) const
{
}

void Connection::deserializeFromJSON(const QJsonObject& obj)
{
}

} // namespace
