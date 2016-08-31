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
    Q_SLOT const QUrl& cacheUrl() const { return _cacheUrl; }
    Q_SLOT void setCacheUrl(const QUrl&);
    Q_SLOT const bool isRunning() const;
    Q_SLOT void setObject(QObject*);
    Q_SLOT void clear();
    Q_SLOT void addNode(const QJsonObject&);
    Q_SLOT void addConnection(const QJsonObject&);
    Q_SLOT void setNodeAttribute(const QString&, const QString&, const QVariant&);
    Q_SLOT QVariant getNodeAttribute(const QString&, const QString&);
    Q_SLOT void startWorker(BuildMode, const QString& = "");
    Q_SLOT void stopWorker();

public:
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void isRunningChanged();
    Q_SIGNAL void cleared();
    Q_SIGNAL void nodeAdded(const QJsonObject& node);
    Q_SIGNAL void connectionAdded(const QJsonObject& node);
    Q_SIGNAL void nodeStatusChanged(const QString&, const QString&);
    Q_SIGNAL void nodeAttributeChanged(const QString&, const QString&, const QVariant&);

public:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QUrl _cacheUrl;
    dg::Ptr<dg::Graph> _graph = nullptr;
    WorkerThread* _worker = nullptr;
    QObject* _qmlObject = nullptr;
};

} // namespace
