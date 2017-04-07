#pragma once

#include <QUndoCommand>
#include "Scene.hpp"

namespace meshroom
{

class UndoCommand : public QUndoCommand
{
public:
    UndoCommand(QUndoCommand* parent = nullptr)
        : QUndoCommand(parent){}
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


class GraphCmd : public UndoCommand
{
public:
    GraphCmd(Graph* graph, QUndoCommand* parent=nullptr)
        : UndoCommand(parent)
    {
        _scene = qobject_cast<Scene*>(graph->parent());
        Q_CHECK_PTR(_scene);
        Q_ASSERT(_scene->graphs()->contains(graph));
        _graphIdx = _scene->graphs()->indexOf(graph);
    }

    Graph* getGraph() const {
        return _scene->graphs()->at(_graphIdx);
    }

private:
    Scene* _scene = nullptr;
    int _graphIdx;
};

class AddNodeCmd : public GraphCmd
{
public:
    AddNodeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent=nullptr)
        : GraphCmd(graph, parent)
        , _desc(desc)
    {}

    bool redoImpl() override
    {
        if(!getGraph()->doAddNode(_desc, _updatedDesc))
            return false;
        setText(QString("Add node %1").arg(_updatedDesc.value("name").toString()));
        return true;
    }
    bool undoImpl() override {
        return getGraph()->doRemoveNode(_updatedDesc);
    }

private:
    QJsonObject _desc;
    QJsonObject _updatedDesc;
};

class MoveNodeCmd : public GraphCmd
{
public:
    MoveNodeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent=nullptr)
        : GraphCmd(graph, parent)
        , _newdesc(desc)
    {
        QString nodename = desc.value("name").toString();
        setText(QString("Move %1").arg(nodename));
        auto guiNodes = getGraph()->nodes();
        auto modelIndex = guiNodes->index(guiNodes->rowIndex(nodename));
        auto* node = guiNodes->data(modelIndex, nodeeditor::NodeCollection::ModelDataRole)
                         .value<nodeeditor::Node*>();
        Q_CHECK_PTR(node);
        _olddesc = node->serializeToJSON();
    }
    bool redoImpl() override { return getGraph()->doMoveNode(_newdesc); }
    bool undoImpl() override { return getGraph()->doMoveNode(_olddesc); }

private:
    QJsonObject _newdesc;
    QJsonObject _olddesc;
};

class RemoveNodeCmd : public GraphCmd
{
public:
    RemoveNodeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent=nullptr)
        : GraphCmd(graph, parent)
        , _desc(desc)
    {
        setText(QString("Remove %1").arg(_desc.value("name").toString()));
    }
    bool redoImpl() override { return getGraph()->doRemoveNode(_desc); }
    bool undoImpl() override
    {
        QJsonObject o;
        bool b = getGraph()->doAddNode(_desc, o);
        QUndoCommand::undo(); // call child commands (AddEdgeCmd(s))
        return b;
    }

private:
    QJsonObject _desc;
};

class AddEdgeCmd : public GraphCmd
{
public:
    AddEdgeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent=nullptr)
        : GraphCmd(graph, parent)
        , _desc(desc)
    {
        setText(QString("Add edge"));
    }
    bool redoImpl() override { return getGraph()->doAddEdge(_desc); }
    bool undoImpl() override { return getGraph()->doRemoveEdge(_desc); }

protected:
    QJsonObject _desc;
};

class RemoveEdgeCmd : public GraphCmd
{
public:
    RemoveEdgeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent = nullptr)
        : GraphCmd(graph, parent)
        , _desc(desc)
    {
        setText(QString("Remove edge"));
    }
    bool redoImpl() override { return getGraph()->doRemoveEdge(_desc); }
    bool undoImpl() override { return getGraph()->doAddEdge(_desc); }

protected:
    QJsonObject _desc;
};

class EditAttributeCmd : public GraphCmd
{
public:
    EditAttributeCmd(Graph* graph, const QJsonObject& desc, QUndoCommand* parent=nullptr)
        : GraphCmd(graph, parent)
        , _newdesc(desc)
    {
        // read node & attribute names
        auto nodename = _newdesc.value("node").toString(); // added dynamically
        auto attributekey = _newdesc.value("key").toString();
        auto attributename = _newdesc.value("name").toString();
        // set command text
        setText(QString("Edit attribute %1.%2").arg(nodename).arg(attributename));
        // store the current attribute description
        auto* node = getGraph()->node(nodename);
        Q_CHECK_PTR(node);
        auto* attribute = node->attribute(attributekey);
        Q_CHECK_PTR(attribute);
        _olddesc = attribute->serializeToJSON();
        _olddesc.insert("node", nodename);
        // ensure value is serialized, even if it's the default one
        if(attribute->hasDefaultValue())
            _olddesc.insert("value", QJsonValue::fromVariant(attribute->value()));
    }
    bool redoImpl() override { return getGraph()->doSetAttribute(_newdesc); }
    bool undoImpl() override { return getGraph()->doSetAttribute(_olddesc); }

protected:
    QJsonObject _newdesc;
    QJsonObject _olddesc;
};

class AddGraphCmd : public UndoCommand
{
public:
    AddGraphCmd(Scene* scene, const QJsonObject& graphdesc=QJsonObject(), int idx=-1, QUndoCommand* parent=nullptr)
        : UndoCommand(parent)
        , _scene(scene)
        , _idx(idx)
        , _graphdesc(graphdesc)
    {
        setText(QString("Add Graph"));
    }
    bool redoImpl() override {
        _graph = _scene->createAndAddGraph(false, _graphdesc, _idx);
        _idx = _scene->graphs()->indexOf(_graph);
        return true;
    }
    bool undoImpl() override {
        _scene->doDeleteGraph(_scene->graphs()->at(_idx));
        return true;
    }

protected:
    Scene* _scene;
    int _idx;
    Graph* _graph;
    QJsonObject _graphdesc;
};

class DeleteGraphCmd : public UndoCommand
{
public:
    DeleteGraphCmd(Scene* scene, int idx, QUndoCommand* parent=nullptr)
        : UndoCommand(parent)
        , _scene(scene)
        , _idx(idx)
    {
        Graph* g = scene->graphs()->at(idx);
        _wasCurrent = scene->graph() == g;
        setText(QString("Delete Graph: %1").arg(g->name()));
        _graphdesc = g->serializeToJSON();
    }
    bool redoImpl() override {
        _scene->doDeleteGraph(_scene->graphs()->at(_idx));
        return true;
    }
    bool undoImpl() override {
        _scene->createAndAddGraph(false, _graphdesc, _idx);
        return true;
    }

protected:
    Scene* _scene;
    int _idx;
    bool _wasCurrent;
    QJsonObject _graphdesc;
};


} // namespace
