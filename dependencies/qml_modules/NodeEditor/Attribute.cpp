#include "Attribute.hpp"
#include <QJsonObject>
#include <QJsonArray>
#include <QJSValue>
#include <QDebug>

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

QJsonObject Attribute::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert(_key, QJsonValue::fromVariant(_value));
    return obj;
}

void Attribute::deserializeFromJSON(const QJsonObject& obj)
{
    auto toEnum = [](const QString& type) -> AttributeType
    {
        if(type == "TEXTFIELD")
            return TEXTFIELD;
        else if(type == "SLIDER")
            return SLIDER;
        else if(type == "COMBOBOX")
            return COMBOBOX;
        else if(type == "CHECKBOX")
            return CHECKBOX;
        return UNKNOWN;
    };

    _value = obj.value("value").toVariant();
    _key = obj.value("key").toString();
    _name = obj.value("name").toString();
    _tooltip = obj.value("tooltip").toString();
    _min = obj.value("min").toVariant();
    _max = obj.value("max").toVariant();
    _step = obj.value("step").toVariant();
    _type = toEnum(obj.value("type").toString());
    for(auto o : obj.value("options").toArray())
        _options.append(o.toString());
}

} // namespace
