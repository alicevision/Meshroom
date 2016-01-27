#include "Attribute.hpp"
#include <QJsonObject>
#include <QJSValue>
#include <QUrl>

namespace meshroom
{

Attribute::Attribute(const Attribute& obj)
    : _value(obj.value())
    , _key(obj.key())
    , _name(obj.name())
    , _type(obj.type())
    , _min(obj.min())
    , _max(obj.max())
    , _step(obj.step())
    , _options(obj.options())
{
}

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
