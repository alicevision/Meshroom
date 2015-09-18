#include "Attribute.hpp"
#include <QJsonObject>
#include <QJSValue>
#include <QUrl>
#include <QDebug>

namespace mockup
{

void Attribute::setValue(const QVariant& value)
{
    if(value == _value)
        return;
    _value = value;
    if(_value.userType() == qMetaTypeId<QJSValue>())
        _value = qvariant_cast<QJSValue>(_value).toVariant();
}

void Attribute::setName(const QString& name)
{
    if(name == _name)
        return;
    _name = name;
}

void Attribute::setType(const int& type)
{
    if(type == _type)
        return;
    _type = type;
}

void Attribute::setMin(const QVariant& min)
{
    if(min == _min)
        return;
    _min = min;
}

void Attribute::setMax(const QVariant& max)
{
    if(max == _max)
        return;
    _max = max;
}

void Attribute::setStep(const QVariant& step)
{
    if(step == _step)
        return;
    _step = step;
}

void Attribute::setOptions(const QStringList& options)
{
    if(options == _options)
        return;
    _options = options;
}

void Attribute::serializeToJSON(QJsonObject* stepObject) const
{
    if(!stepObject)
        return;
    stepObject->insert(_name, QJsonValue::fromVariant(_value));
}

void Attribute::deserializeFromJSON(const QJsonObject& stepObject)
{
    if(!stepObject.contains(_name))
        return;
    QJsonValue attrValue = stepObject.value(_name);
    _value = attrValue.toVariant();
}

} // namespace
