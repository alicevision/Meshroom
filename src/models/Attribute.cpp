#include "Attribute.hpp"
#include <QJsonObject>
#include <QJSValue>
#include <QUrl>
#include <QDebug>

namespace mockup
{

void Attribute::setValue(const QVariant& value)
{
    _value = value;
    if(_value.userType() == qMetaTypeId<QJSValue>())
        _value = qvariant_cast<QJSValue>(_value).toVariant();
}

void Attribute::serializeToJSON(QJsonObject* stepObject) const
{
    if(!stepObject)
        return;
    stepObject->insert(_key, QJsonValue::fromVariant(_value));
}

void Attribute::deserializeFromJSON(const QJsonObject& stepObject)
{
    if(!stepObject.contains(_key))
        return;
    QJsonValue attrValue = stepObject.value(_key);
    _value = attrValue.toVariant();
}

} // namespace
