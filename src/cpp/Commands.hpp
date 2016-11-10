#pragma once

#include <QUndoCommand>
#include "Actions.hpp"

namespace meshroom
{

class UndoCommand : public QUndoCommand
{
public:
    virtual ~UndoCommand() = default;
    virtual bool redoImpl() = 0;
    virtual bool undoImpl() = 0;

public:
    void setEnabled(bool enabled) { _enabled = enabled; }
    void redo() override
    {
        if(!_enabled)
            return;
        redoImpl();
    }
    void undo() override
    {
        if(!_enabled)
            return;
        undoImpl();
    }

private:
    bool _enabled = true;
};

class AddNodeCmd : public UndoCommand
{
public:
    AddNodeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _desc(desc)
    {
    }
    bool redoImpl() override
    {
        if(!AddNodeAction::process(_graph, _desc, _updatedDesc))
            return false;
        setText(QString("Create %1").arg(_updatedDesc.value("name").toString()));
        return true;
    }
    bool undoImpl() override { return RemoveNodeAction::process(_graph, _updatedDesc); }
private:
    Graph* _graph;
    QJsonObject _desc;
    QJsonObject _updatedDesc;
};

class MoveNodeCmd : public UndoCommand
{
public:
    MoveNodeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _newdesc(desc)
    {
        QString nodename = desc.value("name").toString();
        setText(QString("Move %1").arg(nodename));
        Q_CHECK_PTR(graph);
        auto guiNodes = _graph->nodes();
        auto modelIndex = guiNodes->index(guiNodes->rowIndex(nodename));
        auto* node = guiNodes->data(modelIndex, nodeeditor::NodeCollection::ModelDataRole)
                         .value<nodeeditor::Node*>();
        Q_CHECK_PTR(node);
        _olddesc = node->serializeToJSON();
    }
    bool redoImpl() override { return MoveNodeAction::process(_graph, _newdesc); }
    bool undoImpl() override { return MoveNodeAction::process(_graph, _olddesc); }
private:
    Graph* _graph;
    QJsonObject _newdesc;
    QJsonObject _olddesc;
};

class RemoveNodeCmd : public UndoCommand
{
public:
    RemoveNodeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _desc(desc)
    {
        setText(QString("Remove %1").arg(_desc.value("name").toString()));
    }
    bool redoImpl() override { return RemoveNodeAction::process(_graph, _desc); }
    bool undoImpl() override
    {
        QJsonObject o;
        return AddNodeAction::process(_graph, _desc, o);
    }

private:
    Graph* _graph;
    QJsonObject _desc;
};

class AddEdgeCmd : public UndoCommand
{
public:
    AddEdgeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _desc(desc)
    {
        setText(QString("Add edge"));
    }
    bool redoImpl() override { return AddEdgeAction::process(_graph, _desc); }
    bool undoImpl() override { return RemoveEdgeAction::process(_graph, _desc); }
protected:
    Graph* _graph;
    QJsonObject _desc;
};

class RemoveEdgeCmd : public UndoCommand
{
public:
    RemoveEdgeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _desc(desc)
    {
        setText(QString("Remove edge"));
    }
    bool redoImpl() override { return RemoveEdgeAction::process(_graph, _desc); }
    bool undoImpl() override { return AddEdgeAction::process(_graph, _desc); }
protected:
    Graph* _graph;
    QJsonObject _desc;
};

class EditAttributeCmd : public UndoCommand
{
public:
    EditAttributeCmd(Graph* graph, const QJsonObject& desc)
        : _graph(graph)
        , _newdesc(desc)
    {
        // read node & attribute names
        auto nodename = _newdesc.value("node").toString(); // added dynamically
        auto attributekey = _newdesc.value("key").toString();
        auto attributename = _newdesc.value("name").toString();
        // set command text
        setText(QString("Edit attribute %1.%2").arg(nodename).arg(attributename));
        // store the current attribute description
        Q_CHECK_PTR(graph);
        auto* node = graph->node(nodename);
        Q_CHECK_PTR(node);
        auto* attribute = node->attribute(attributekey);
        Q_CHECK_PTR(attribute);
        _olddesc = attribute->serializeToJSON();
        _olddesc.insert("node", nodename);
    }
    bool redoImpl() override { return EditAttributeAction::process(_graph, _newdesc); }
    bool undoImpl() override { return EditAttributeAction::process(_graph, _olddesc); }
protected:
    Graph* _graph;
    QJsonObject _newdesc;
    QJsonObject _olddesc;
};

} // namespace
