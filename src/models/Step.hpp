#pragma once

#include <QObject>
#include "AttributeModel.hpp"

namespace meshroom
{

class Step : public QObject
{
    Q_OBJECT

public:
    Step(const QString& name);

public:
    const QString& name() const { return _name; }
    AttributeModel* attributes() const { return _attributes; }

public:
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    QString _name;
    AttributeModel* _attributes;
};

} // namespace
