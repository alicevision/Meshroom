#pragma once

#include "WorkerThread.hpp"
#include "Worker.hpp"
#include <nodeEditor/AbstractGraph.hpp>
#include <dglib/dg.hpp>

namespace meshroom
{

class Application; // forward declaration

class Graph : public nodeeditor::AbstractGraph
{
    Q_OBJECT
    Q_PROPERTY(QUrl cacheUrl READ cacheUrl WRITE setCacheUrl NOTIFY cacheUrlChanged)
    Q_PROPERTY(bool isRunning READ isWorkerThreadRunning NOTIFY isRunningChanged)

public:
    Graph(QObject* parent = nullptr);
    ~Graph();
    Q_INVOKABLE void clear() override;
    Q_INVOKABLE bool addNode(const QJsonObject&) override;
    Q_INVOKABLE bool addEdge(const QJsonObject&) override;
    Q_INVOKABLE bool removeNode(const QJsonObject&) override;
    Q_INVOKABLE bool removeEdge(const QJsonObject&) override;
    Q_INVOKABLE bool setAttribute(const QJsonObject&) override;
    Q_INVOKABLE QJsonObject serializeToJSON() const override;
    Q_INVOKABLE void deserializeFromJSON(const QJsonObject&) override;

public:
    dg::Graph& coreGraph() { return _graph; }
    Q_SLOT QUrl cacheUrl() const;
    Q_SLOT void setCacheUrl(const QUrl&);

    bool _addNode(const QJsonObject& desc);
    bool _addNode(const QJsonObject& desc, QJsonObject& updatedDesc);
    bool _addEdge(const QJsonObject&);
    bool _removeNode(const QJsonObject&);
    bool _removeEdge(const QJsonObject&);

public:
    // worker
    Q_SLOT void startWorkerThread(meshroom::Worker::Mode, const QString&);
    Q_SLOT void stopWorkerThread();
    Q_SLOT bool isWorkerThreadRunning() const;

public:
    Q_SIGNAL void dataChanged();
    Q_SIGNAL void nodeNameChanged(const QString&, const QString&);
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void isRunningChanged();

private:
    dg::Graph _graph;
    WorkerThread* _thread = nullptr;
    Application* _application = nullptr;
};

} // namespace
