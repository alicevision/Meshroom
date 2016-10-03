#include "Attribute.hpp"
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
    Q_EMIT valueChanged();
}

QJsonObject Attribute::serializeToJSON() const
{
    auto toString = [](const AttributeType& type) -> QString
    {
        switch(type)
        {
            case TEXTFIELD:
                return "TEXTFIELD";
            case SLIDER:
                return "SLIDER";
            case COMBOBOX:
                return "COMBOBOX";
            case CHECKBOX:
                return "CHECKBOX";
            case IMAGELIST:
                return "IMAGELIST";
            case OBJECT3D:
                return "OBJECT3D";
            default:
                return "UNKNOWN";
        }
    };

    QJsonObject obj;
    obj.insert("key", _key);
    obj.insert("name", _name);
    obj.insert("type", toString(_type));
    if(!_value.isNull())
        obj.insert("value", QJsonValue::fromVariant(_value));
    if(!_min.isNull())
        obj.insert("min", QJsonValue::fromVariant(_min));
    if(!_max.isNull())
        obj.insert("max", QJsonValue::fromVariant(_max));
    if(!_step.isNull())
        obj.insert("step", QJsonValue::fromVariant(_step));
    if(!_options.isEmpty())
        obj.insert("options", QJsonValue::fromVariant(_options));
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
        else if(type == "IMAGELIST")
            return IMAGELIST;
        else if(type == "OBJECT3D")
            return OBJECT3D;
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
