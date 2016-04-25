#pragma once

#include <QObject>
#include "AttributeModel.hpp"

namespace nodeeditor
{

class Node : public QObject
{
    Q_OBJECT

public:
    Node() = default;
    Node(const QString& name);
    Node(const Node& obj);

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
