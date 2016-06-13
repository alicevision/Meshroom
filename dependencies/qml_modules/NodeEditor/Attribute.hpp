#pragma once

#include <QObject>
#include <QVariant>

namespace nodeeditor
{

class Attribute : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QVariant value READ value WRITE setValue NOTIFY valueChanged)
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QString key READ key CONSTANT)
    Q_PROPERTY(QString tooltip READ tooltip CONSTANT)
    Q_PROPERTY(AttributeType type READ type CONSTANT)
    Q_PROPERTY(QVariant min READ min CONSTANT)
    Q_PROPERTY(QVariant max READ max CONSTANT)
    Q_PROPERTY(QVariant step READ step CONSTANT)
    Q_PROPERTY(QStringList options READ options CONSTANT)

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
        IMAGELIST
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
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject& obj);

public:
    Q_SIGNAL void valueChanged();

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
};

} // namespace
