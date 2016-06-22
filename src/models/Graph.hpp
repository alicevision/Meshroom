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
        LOCAL = 0,
        TRACTOR = 1
    };
    Q_ENUMS(BuildMode)

public:
    Graph(QObject* parent = nullptr);
    ~Graph();

public:
    Q_SLOT const QUrl& cacheUrl() const { return _cacheUrl; }
    Q_SLOT const bool isRunning() const;
    Q_SLOT void setCacheUrl(const QUrl&);
    Q_SLOT void setObject(QObject*);

public:
    Q_SLOT void clear();
    Q_SLOT void addNode(const QJsonObject&);
    Q_SLOT void addConnection(const QJsonObject&);
    Q_SLOT void setAttribute(const QString& nodeName, const QJsonObject& descriptor);
    Q_SLOT void startWorker(const QString&, BuildMode mode);
    Q_SLOT void stopWorker();

public:
    Q_SIGNAL void cacheUrlChanged();
    Q_SIGNAL void isRunningChanged();
    Q_SIGNAL void cleared();
    Q_SIGNAL void nodeAdded(const QJsonObject& node);
    Q_SIGNAL void connectionAdded(const QJsonObject& node);
    Q_SIGNAL void nodeStatusChanged(const QString&, const QString&);

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
