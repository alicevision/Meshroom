#pragma once

#include "Worker.hpp"
#include <QObject>
#include <QUrl>
#include <dglib/dg.hpp>

namespace meshroom
{

class Application;  // forward declaration
class WorkerThread; // forward declaration

class Graph : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl cacheUrl READ cacheUrl WRITE setCacheUrl NOTIFY cacheUrlChanged)
    Q_PROPERTY(bool isRunning READ isWorkerThreadRunning NOTIFY isRunningChanged)

public:
    Graph(QObject* parent = nullptr);
    ~Graph();

public:
    // graph editing
    Q_SLOT void clear();
    Q_SLOT bool addNode(const QJsonObject&);
    Q_SLOT bool addEdge(const QJsonObject&);
    Q_SLOT bool removeNode(const QJsonObject&);
    Q_SLOT bool removeEdge(const QJsonObject&);
    Q_SLOT void setNodeAttribute(const QString&, const QString&, const QVariant&);
    Q_SLOT QVariant getNodeAttribute(const QString&, const QString&);
    Q_SLOT QUrl cacheUrl() const;
    Q_SLOT void setCacheUrl(const QUrl&);
    // worker
    Q_SLOT void startWorkerThread(meshroom::Worker::Mode, const QString&);
    Q_SLOT void stopWorkerThread();
    Q_SLOT bool isWorkerThreadRunning() const;

public:
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void dataChanged();
    Q_SIGNAL void isRunningChanged();

private:
    Q_SIGNAL void nodeRenamed(const QString&, const QString&);

public:
    dg::Graph& dggraph() { return _dggraph; }
    void registerQmlObject(QObject* obj) { _editor = obj; }
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    dg::Graph _dggraph;
    WorkerThread* _thread = nullptr;
    QObject* _editor = nullptr;
};

#define GET_METHOD_OR_RETURN(prototype, returnArg)                                                 \
    if(!_editor)                                                                                   \
        return returnArg;                                                                          \
    const QMetaObject* metaObject = _editor->metaObject();                                         \
    int methodIndex = metaObject->indexOfSlot(QMetaObject::normalizedSignature(#prototype));       \
    if(methodIndex == -1)                                                                          \
    {                                                                                              \
        qCritical() << "can't invoke function" << #prototype;                                      \
        return returnArg;                                                                          \
    }                                                                                              \
    QMetaMethod method = metaObject->method(methodIndex);

} // namespace
