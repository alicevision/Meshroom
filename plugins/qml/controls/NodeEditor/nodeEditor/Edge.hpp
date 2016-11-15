#pragma once

#include "Node.hpp"
#include <QObject>
#include <QJsonObject>

namespace nodeeditor
{

class Edge : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString source READ source WRITE setSource NOTIFY sourceChanged)
    Q_PROPERTY(QString target READ target WRITE setTarget NOTIFY targetChanged)
    Q_PROPERTY(QString plug READ plug WRITE setPlug NOTIFY plugChanged)

public:
    Edge(NodeCollection&);
    Edge(const Edge& obj) = delete;
    Edge& operator=(Edge const&) = delete;

public:
    Q_SLOT QString source() const { return _sourceNode ? _sourceNode->name() : ""; }
    Q_SLOT QString target() const { return _targetNode ? _targetNode->name() : ""; }
    Q_SLOT QString plug() const { return _targetAttribute ? _targetAttribute->key() : ""; }
    Q_SLOT Attribute* sourceAttribute() const { return _sourceAttribute; }
    Q_SLOT Attribute* targetAttribute() const { return _targetAttribute; }
    Q_SLOT void setSource(const QString&);
    Q_SLOT void setTarget(const QString&);
    Q_SLOT void setPlug(const QString&);
    Q_SIGNAL void sourceChanged();
    Q_SIGNAL void targetChanged();
    Q_SIGNAL void plugChanged();

public:
    Q_SLOT QJsonObject serializeToJSON() const;
    Q_SLOT void deserializeFromJSON(const QJsonObject& obj);

private:
    Node* _sourceNode = nullptr;
    Node* _targetNode = nullptr;
    Attribute* _sourceAttribute = nullptr;
    Attribute* _targetAttribute = nullptr;
    NodeCollection& _nodes;
};

inline Edge::Edge(NodeCollection& nodes)
    : _nodes(nodes)
{
}

inline void Edge::setSource(const QString& source)
{
    if(_sourceNode && _sourceNode->name() == source)
        return;

    auto getNodePtr = [&](const QString& n) -> Node*
    {
        auto id = _nodes.index(_nodes.rowIndex(n));
        QVariant v = _nodes.data(id, nodeeditor::NodeCollection::ModelDataRole);
        auto node = v.value<nodeeditor::Node*>();
        Q_CHECK_PTR(node);
        return node;
    };
    _sourceNode = getNodePtr(source);

    auto getAttrPtr = [&]() -> Attribute*
    {
        auto id = _sourceNode->outputs()->index(0);
        QVariant v =
            _sourceNode->outputs()->data(id, nodeeditor::AttributeCollection::ModelDataRole);
        auto attr = v.value<nodeeditor::Attribute*>();
        Q_CHECK_PTR(attr);
        return attr;
    };
    _sourceAttribute = getAttrPtr();

    Q_EMIT sourceChanged();
}

inline void Edge::setTarget(const QString& target)
{
    if(_targetNode && _targetNode->name() == target)
        return;

    auto getNodePtr = [&](const QString& n) -> Node*
    {
        auto id = _nodes.index(_nodes.rowIndex(n));
        QVariant v = _nodes.data(id, nodeeditor::NodeCollection::ModelDataRole);
        auto node = v.value<nodeeditor::Node*>();
        Q_CHECK_PTR(node);
        return node;
    };
    _targetNode = getNodePtr(target);

    Q_EMIT targetChanged();
}

inline void Edge::setPlug(const QString& plug)
{
    if(_targetAttribute && _targetAttribute->key() == plug)
        return;

    if(!_targetNode)
        return;

    auto getAttrPtr = [&](const QString& a) -> Attribute*
    {
        auto id = _targetNode->inputs()->index(_targetNode->inputs()->rowIndex(a));
        QVariant v =
            _targetNode->inputs()->data(id, nodeeditor::AttributeCollection::ModelDataRole);
        auto attr = v.value<nodeeditor::Attribute*>();
        Q_CHECK_PTR(attr);
        return attr;
    };
    _targetAttribute = getAttrPtr(plug);

    Q_EMIT plugChanged();
}

inline QJsonObject Edge::serializeToJSON() const
{
    QJsonObject obj;
    obj.insert("source", _sourceNode->name());
    obj.insert("target", _targetNode->name());
    obj.insert("plug", _targetAttribute->key());
    return obj;
}

inline void Edge::deserializeFromJSON(const QJsonObject& obj)
{
    if(obj.contains("source"))
        setSource(obj.value("source").toString());
    if(obj.contains("target"))
        setTarget(obj.value("target").toString());
    if(obj.contains("plug"))
        setPlug(obj.value("plug").toString());
}

} // namespace
