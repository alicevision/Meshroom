#pragma once

#include <QObject>
#include <QVariant>
#include <QJsonObject>

namespace nodeeditor
{

class AttributeCollection;

class Attribute : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QVariant value READ value NOTIFY valueChanged)
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QString key READ key CONSTANT)
    Q_PROPERTY(QString tooltip READ tooltip CONSTANT)
    Q_PROPERTY(AttributeType type READ type CONSTANT)
    Q_PROPERTY(QVariant min READ min CONSTANT)
    Q_PROPERTY(QVariant max READ max CONSTANT)
    Q_PROPERTY(QVariant step READ step CONSTANT)
    Q_PROPERTY(QStringList options READ options CONSTANT)
    Q_PROPERTY(QObjectList connections MEMBER _connections NOTIFY connectionsChanged)
    Q_PROPERTY(bool isConnected READ isConnected NOTIFY connectionsChanged)

public:
    Attribute() = default;
    Attribute(const Attribute& obj);

public:
    enum AttributeType
    {
        UNKNOWN = 0,
        TEXTFIELD,
        SLIDER,
        COMBOBOX,
        CHECKBOX,
        IMAGELIST,
        OBJECT3D
    };
    Q_ENUMS(AttributeType)

public:
    QVariant value() const { return _value; }
    QString key() const { return _key; }
    QString name() const { return _name; }
    QString tooltip() const { return _tooltip; }
    const AttributeType& type() const { return _type; }
    const QVariant& min() const { return _min; }
    const QVariant& max() const { return _max; }
    const QVariant& step() const { return _step; }
    const QStringList& options() const { return _options; }
    bool isConnected() const { return !_connections.isEmpty(); }
    void setValue(const QVariant& value);
    void setKey(const QString& key) { _key = key; }
    void setName(const QString& name) { _name = name; }
    void setTooltip(const QString& tooltip) { _tooltip = tooltip; }
    void setType(const AttributeType& type) { _type = type; }
    void setMin(const QVariant& min) { _min = min; }
    void setMax(const QVariant& max) { _max = max; }
    void setStep(const QVariant& step) { _step = step; }
    void setOptions(const QStringList& options) { _options = options; }

public:
    Q_SLOT QJsonObject serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonObject& obj);

public:
    Q_SIGNAL void valueChanged();
    Q_SIGNAL void connectionsChanged();

private:
    friend class EdgeCollection;
    void addConnection(Attribute*);
    void removeConnection(Attribute*);

private:
    QVariant _value;
    QString _key;
    QString _name;
    QString _tooltip;
    AttributeType _type = AttributeType::UNKNOWN;
    QVariant _min;
    QVariant _max;
    QVariant _step;
    QStringList _options;
    QObjectList _connections;
};

inline Attribute::Attribute(const Attribute& obj)
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

inline void Attribute::setValue(const QVariant& value)
{
    _value = value;
    Q_EMIT valueChanged();
}

inline QJsonObject Attribute::serializeToJSON() const
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

inline void Attribute::deserializeFromJSON(const QJsonObject& obj)
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

    if(obj.contains("value"))
        _value = obj.value("value").toVariant();
    if(obj.contains("key"))
        _key = obj.value("key").toString();
    if(obj.contains("name"))
        _name = obj.value("name").toString();
    if(obj.contains("tooltip"))
        _tooltip = obj.value("tooltip").toString();
    if(obj.contains("min"))
        _min = obj.value("min").toVariant();
    if(obj.contains("max"))
        _max = obj.value("max").toVariant();
    if(obj.contains("step"))
        _step = obj.value("step").toVariant();
    if(obj.contains("type"))
        _type = toEnum(obj.value("type").toString());
    if(obj.contains("options"))
    {
        _options.clear();
        for(auto o : obj.value("options").toArray())
            _options.append(o.toString());
    }
}

inline void Attribute::addConnection(Attribute* a)
{
    _connections.append(a);
    Q_EMIT connectionsChanged();
}

inline void Attribute::removeConnection(Attribute* a)
{
    _connections.removeOne(a);
    Q_EMIT connectionsChanged();
}

} // namespace
