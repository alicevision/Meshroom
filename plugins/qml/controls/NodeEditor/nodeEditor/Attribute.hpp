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
    Q_PROPERTY(QVariant defaultValue MEMBER _defaultValue CONSTANT)
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
    /// Return whether the current value is equal to the default value
    bool hasDefaultValue() const;

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
    QVariant _defaultValue;
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
    if(_value == value)
        return;
    _value = value;
    Q_EMIT valueChanged();
}
inline bool Attribute::hasDefaultValue() const
{
    return _value == _defaultValue;
}


inline QJsonObject Attribute::serializeToJSON() const
{
    // Serialize only the data:
    //  - related to identification (key)
    //  - not contained in the node definition (non-default value)
    QJsonObject obj;
    obj.insert("key", _key);
    if(!hasDefaultValue())
        obj.insert("value", QJsonValue::fromVariant(_value));
    return obj;
}

inline void Attribute::deserializeFromJSON(const QJsonObject& obj)
{
    // Deserialization of an attribute should come from the deserialization
    // of a plugin node definition, hence contain the 'type' key.
    Q_ASSERT_X(obj.contains("type"),
               "deserializeFromJSON",
               "Missing 'type' key. Can only deserialize an attribute from a node definition");

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

    _type = toEnum(obj.value("type").toString());

    if(obj.contains("value"))
    {
        // Store value as default and initial value
        _defaultValue = obj.value("value").toVariant();
        _value = _defaultValue;
    }
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
