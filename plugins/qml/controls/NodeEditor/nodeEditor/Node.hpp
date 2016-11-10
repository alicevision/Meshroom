#pragma once

#include <QObject>
#include <QJsonObject>
#include <QPoint>
#include "AttributeCollection.hpp"

namespace nodeeditor
{

class Node : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name CONSTANT)
    Q_PROPERTY(QString type READ type CONSTANT)
    Q_PROPERTY(AttributeCollection* inputs READ inputs CONSTANT)
    Q_PROPERTY(AttributeCollection* outputs READ outputs CONSTANT)
    Q_PROPERTY(Status status READ status WRITE setStatus NOTIFY statusChanged)
    Q_PROPERTY(QPoint position READ position WRITE setPosition NOTIFY positionChanged)

public:
    enum Status
    {
        READY = 0,
        WAITING,
        RUNNING,
        ERROR,
        DONE
    };
    Q_ENUMS(Status)

public:
    Node() = default;
    Node(const Node& obj) = delete;
    Node& operator=(Node const&) = delete;

public:
    const QString& name() const { return _name; }
    const QString& type() const { return _type; }
    AttributeCollection* inputs() const { return _inputs; }
    AttributeCollection* outputs() const { return _outputs; }
    Attribute* attribute(const QString&) const;
    Status status() const { return _status; }
    void setStatus(Status);
    QPoint position() const { return _position; }
    void setPosition(const QPoint& value);

public:
    Q_INVOKABLE QJsonObject serializeToJSON() const;
    Q_INVOKABLE void deserializeFromJSON(const QJsonObject& obj);

public:
    Q_SIGNAL void statusChanged();
    Q_SIGNAL void positionChanged(QPoint oldPos);
    Q_SIGNAL void requestPositionUpdate(QPoint position);

private:
    QString _name = "unknown";
    QString _type = "Unknown";
    AttributeCollection* _inputs = new AttributeCollection(this);
    AttributeCollection* _outputs = new AttributeCollection(this);
    Status _status = READY;
    QPoint _position;
};

inline Attribute* Node::attribute(const QString& key) const
{
    auto getAttrFromCollection = [&](
        nodeeditor::AttributeCollection* collection) -> nodeeditor::Attribute*
    {
        int id = collection->rowIndex(key);
        if(id < 0)
            return nullptr;
        auto modelIndex = collection->index(id);
        return collection->data(modelIndex, nodeeditor::AttributeCollection::ModelDataRole)
            .value<nodeeditor::Attribute*>();
    };
    Attribute* attribute = getAttrFromCollection(_inputs);
    if(attribute)
        return attribute;
    return getAttrFromCollection(_outputs);
}

inline void Node::setStatus(Status status)
{
    if(_status == status)
        return;
    _status = status;
    Q_EMIT statusChanged();
}

inline void Node::setPosition(const QPoint& value)
{
    if(_position == value)
        return;
    _position = value;
    Q_EMIT positionChanged(value);
}

inline QJsonObject Node::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("name", _name);
    obj.insert("type", _type);
    obj.insert("x", _position.x());
    obj.insert("y", _position.y());
    obj.insert("inputs", _inputs->serializeToJSON());
    obj.insert("outputs", _outputs->serializeToJSON());
    return obj;
}

inline void Node::deserializeFromJSON(const QJsonObject& obj)
{
    if(obj.contains("name"))
        _name = obj.value("name").toString();
    if(obj.contains("type"))
        _type = obj.value("type").toString();
    if(obj.contains("x") && obj.contains("y"))
        _position = QPoint(obj.value("x").toInt(), obj.value("y").toInt());
    for(auto o : obj.value("inputs").toArray())
    {
        Attribute* a = new Attribute;
        a->deserializeFromJSON(o.toObject());
        _inputs->add(a);
    }
    for(auto o : obj.value("outputs").toArray())
    {
        Attribute* a = new Attribute;
        a->deserializeFromJSON(o.toObject());
        _outputs->add(a);
    }
}

} // namespace
