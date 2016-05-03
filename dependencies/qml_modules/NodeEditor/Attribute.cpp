#include "Attribute.hpp"
#include <QJsonObject>
#include <QJSValue>

namespace nodeeditor
{

Attribute::Attribute(const Attribute& obj)
    : _value(obj.value())
    , _key(obj.key())
    , _name(obj.name())
    , _tooltip(obj.tooltip())
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

void Attribute::serializeToJSON(QJsonObject* obj) const
{
    if(!obj)
        return;
    obj->insert(_key, QJsonValue::fromVariant(_value));
}

void Attribute::deserializeFromJSON(const QJsonObject& obj)
{
    if(!obj.contains(_key))
        return;
    QJsonValue attrValue = obj.value(_key);
    _value = attrValue.toVariant();
}

} // namespace
