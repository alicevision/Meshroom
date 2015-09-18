#pragma once

#include <QObject>
#include <QVariant>

namespace mockup
{

class Attribute : public QObject
{
    Q_OBJECT

public:
    Attribute() = default;

public:
    QVariant value() const { return _value; }
    QString name() const { return _name; }
    const int& type() const { return _type; }
    const QVariant& min() const { return _min; }
    const QVariant& max() const { return _max; }
    const QVariant& step() const { return _step; }
    const QStringList& options() const { return _options; }
    void setValue(const QVariant& value);
    void setName(const QString& name);
    void setType(const int& type);
    void setMin(const QVariant& min);
    void setMax(const QVariant& max);
    void setStep(const QVariant& step);
    void setOptions(const QStringList& options);

public:
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    QVariant _value;
    QString _name;
    int _type;
    QVariant _min;
    QVariant _max;
    QVariant _step;
    QStringList _options;
};

} // namespace
