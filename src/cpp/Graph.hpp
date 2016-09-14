#pragma once

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
    Q_PROPERTY(bool isRunning READ isRunning NOTIFY isRunningChanged)

public:
    enum BuildMode
    {
        COMPUTE_LOCAL = 0,
        COMPUTE_TRACTOR = 1,
        PREPARE = 2,
    };
    Q_ENUMS(BuildMode)

public:
    Graph(QObject* parent = nullptr);
    ~Graph();

public:
    // graph editing
    Q_SLOT void clear();
    Q_SLOT void addNode(const QJsonObject&);
    Q_SLOT void addConnection(const QJsonObject&);
    Q_SLOT void setNodeAttribute(const QString&, const QString&, const QVariant&);
    Q_SLOT QVariant getNodeAttribute(const QString&, const QString&);
    Q_SLOT const QUrl& cacheUrl() const { return _cacheUrl; }
    Q_SLOT void setCacheUrl(const QUrl&);

    // worker
    Q_SLOT void startWorker(BuildMode, const QString& = "");
    Q_SLOT void stopWorker();
    Q_SLOT const bool isRunning() const;

public:
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void isRunningChanged();

public:
    void registerQmlObject(QObject* obj) { _qmlEditor = obj; }
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QUrl _cacheUrl;
    dg::Ptr<dg::Graph> _graph = nullptr;
    WorkerThread* _worker = nullptr;
    QObject* _qmlEditor = nullptr;
};

#define GET_METHOD_OR_RETURN(prototype, returnArg)                                                 \
    if(!_qmlEditor)                                                                                \
        return returnArg;                                                                          \
    const QMetaObject* metaObject = _qmlEditor->metaObject();                                      \
    int methodIndex = metaObject->indexOfSlot(QMetaObject::normalizedSignature(#prototype));       \
    if(methodIndex == -1)                                                                          \
    {                                                                                              \
        qCritical() << "can't invoke function" << #prototype;                                      \
        return returnArg;                                                                          \
    }                                                                                              \
    QMetaMethod method = metaObject->method(methodIndex);

} // namespace
