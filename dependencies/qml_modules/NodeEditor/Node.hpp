#pragma once

#include <QObject>
#include "AttributeModel.hpp"

namespace nodeeditor
{

class Node : public QObject
{
    Q_OBJECT
    Q_PROPERTY(AttributeModel* inputs READ inputs CONSTANT)
    Q_PROPERTY(AttributeModel* outputs READ outputs CONSTANT)

public:
    Node();
    Node(const QString& name);
    Node(const Node& obj);

public:
    const QString& name() const { return _name; }
    AttributeModel* inputs() const { return _inputs; }
    AttributeModel* outputs() const { return _outputs; }

public:
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

private:
    QString _name;
    AttributeModel* _inputs;
    AttributeModel* _outputs;
};

} // namespace
