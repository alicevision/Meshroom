#pragma once

#include <QObject>
#include <QVariant>

namespace meshroom
{

class Attribute : public QObject
{
    Q_OBJECT

public:
    Attribute() = default;
    Attribute(const Attribute& obj);

public:
    QVariant value() const { return _value; }
    QString key() const { return _key; }
    QString name() const { return _name; }
    QString tooltip() const { return _tooltip; }
    const int& type() const { return _type; }
    const QVariant& min() const { return _min; }
    const QVariant& max() const { return _max; }
    const QVariant& step() const { return _step; }
    const QStringList& options() const { return _options; }
    void setValue(const QVariant& value);
    void setKey(const QString& key) { _key = key; }
    void setName(const QString& name) { _name = name; }
    void setTooltip(const QString& tooltip) { _tooltip = tooltip; }
    void setType(const int& type) { _type = type; }
    void setMin(const QVariant& min) { _min = min; }
    void setMax(const QVariant& max) { _max = max; }
    void setStep(const QVariant& step) { _step = step; }
    void setOptions(const QStringList& options) { _options = options; }

public:
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    QVariant _value;
    QString _key;
    QString _name;
    QString _tooltip;
    int _type;
    QVariant _min;
    QVariant _max;
    QVariant _step;
    QStringList _options;
};

} // namespace
