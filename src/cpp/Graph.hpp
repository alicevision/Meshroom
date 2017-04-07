#pragma once

#include "WorkerThread.hpp"
#include "Worker.hpp"
#include <nodeEditor/AbstractGraph.hpp>
#include <dglib/dg.hpp>

namespace meshroom
{

class Application; // forward declaration
class UndoCommand; // forward declaration
class UndoStack;

class Graph : public nodeeditor::AbstractGraph
{
    Q_OBJECT
    Q_PROPERTY(QString name MEMBER _name READ name NOTIFY nameChanged)
    Q_PROPERTY(QUrl cacheUrl READ cacheUrl WRITE setCacheUrl NOTIFY cacheUrlChanged)
    Q_PROPERTY(bool isRunning READ isWorkerThreadRunning NOTIFY isRunningChanged)

public:
    Graph(QObject* parent = nullptr);
    ~Graph();

public:
    Q_INVOKABLE void clear() override;
    Q_INVOKABLE bool addNode(const QJsonObject&) override;
    Q_INVOKABLE bool addEdge(const QJsonObject&) override;
    Q_INVOKABLE bool removeNode(const QJsonObject&) override;
    Q_INVOKABLE bool removeEdge(const QJsonObject&) override;
    Q_INVOKABLE bool moveNode(const QJsonObject&) override;
    Q_INVOKABLE bool setAttribute(const QJsonObject&) override;
    Q_INVOKABLE QJsonObject serializeToJSON() const override;
    Q_INVOKABLE void deserializeFromJSON(const QJsonObject&) override;
    void deserializeFromJSON(const QJsonObject&, bool generateCommands);

    bool doAddNode(const QJsonObject& descriptor, QJsonObject& updatedDescriptor);
    bool doAddEdge(const QJsonObject& descriptor);
    bool doRemoveNode(const QJsonObject& descriptor);
    bool doRemoveEdge(const QJsonObject& descriptor);
    bool doMoveNode(const QJsonObject& descriptor);
    bool doSetAttribute(const QJsonObject& descriptor);

public:
    dg::Graph& coreGraph() { return _graph; }
    dg::Cache& coreCache() { return _cache; }
    dg::Environment& coreEnvironment() { return _environment; }
    QString name() const { return _name; }
    Q_SLOT QUrl cacheUrl() const;
    Q_SLOT void setCacheUrl(const QUrl&);
    void refreshStatus();

public:
    // worker
    Q_SLOT void startWorkerThread(meshroom::Worker::Mode, const QString&);
    Q_SLOT void stopWorkerThread();
    Q_SLOT bool isWorkerThreadRunning() const;

public:
    Q_SIGNAL void nameChanged(const QString&);
    Q_SIGNAL void nodeNameChanged(const QString&, const QString&);
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void isRunningChanged();

private:
    QString _name = "Graph";
    dg::Graph _graph;
    dg::Cache _cache;
    dg::Environment _environment;
    WorkerThread* _thread = nullptr;
    UndoCommand* _lastCmd = nullptr; // used in callbacks to register child commands
    UndoStack* _undoStack = nullptr;
    bool _nodesStatusDirty = false;
};

} // namespace
