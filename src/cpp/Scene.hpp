#pragma once

#include "Graph.hpp"
#include "UndoStack.hpp"
#include "QQmlObjectListModel.hpp"
#include <QObject>
#include <QUrl>
#include <QDateTime>
#include <QProcess>
#include <QJsonObject>

namespace meshroom
{

class Scene : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url NOTIFY urlChanged)
    Q_PROPERTY(QString name READ name NOTIFY nameChanged)
    Q_PROPERTY(QDateTime date READ date NOTIFY dateChanged)
    Q_PROPERTY(QString user READ user NOTIFY userChanged)
    Q_PROPERTY(QUrl cacheUrl MEMBER _cacheUrl WRITE setCacheUrl NOTIFY cacheUrlChanged)
    Q_PROPERTY(QUrl thumbnail READ thumbnail WRITE setThumbnail NOTIFY thumbnailChanged)
    Q_PROPERTY(UndoStack* undoStack READ undoStack CONSTANT)
    Q_PROPERTY(QObject* graphs READ graphs CONSTANT)
    Q_PROPERTY(Graph* graph READ graph WRITE setGraph NOTIFY graphChanged)

public:
    Scene();
    Scene(QObject* parent, const QUrl& = QUrl());

public:
    Q_SLOT const QUrl& url() const { return _url; }
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT const QDateTime& date() const { return _date; }
    Q_SLOT const QString& user() const { return _user; }
    Q_SLOT void setCacheUrl(const QUrl&);
    Q_SLOT const QUrl& thumbnail() const { return _thumbnail; }
    Q_SLOT Graph* graph() const { return _graph; }
    Q_SLOT int currentGraphIdx() const { return  _graph ? _graphs.indexOf(_graph) : -1; }
    Q_SLOT QQmlObjectListModel<Graph>* graphs() { return &_graphs; }
    Q_SLOT UndoStack* undoStack() { return _undoStack; }

    Q_SLOT void setThumbnail(const QUrl&);
    Q_SLOT bool load(const QUrl&);
    Q_SLOT bool import(const QUrl&);
    Q_SLOT bool save();
    Q_SLOT bool saveAs(const QUrl&);
    Q_SLOT void erase();
    Q_SLOT void reset();
    Q_SLOT void clear();
    Q_SLOT void addGraph(bool makeCurrent);
    Q_SLOT void duplicateGraph(Graph* graph, bool makeCurrent);
    Q_SLOT void deleteGraph(Graph* graph);

    Q_SIGNAL void urlChanged();
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void dateChanged();
    Q_SIGNAL void userChanged();
    Q_SIGNAL void thumbnailChanged();
    Q_SIGNAL void graphChanged();
    Q_SIGNAL void cacheUrlChanged();

    /// Set the given graph as the current one
    void setGraph(Graph* graph);
    void setGraph(int idx) { setGraph(_graphs.at(idx)); }

    /// Create a new Graph (based on graphdesc if valid) and add it to the Scene at index idx
    Graph* createAndAddGraph(bool makeCurrent, const QJsonObject& graphdesc=QJsonObject(), int idx=-1);
    /// Add the given Graph to the scene at index idx
    void addGraph(Graph* graph, int idx=-1);
    /// Remove the given grah from the Scene and delete it
    void doDeleteGraph(Graph* graph);

    /// Whether graphs should update their status when attributes values change
    void setAutoRefresh(bool value)
    {
        _autoRefresh = value;
    }

private:
    void setUrl(const QUrl&);
    void setName(const QString&);
    void setDate(const QDateTime&);
    void setUser(const QString&);

private:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    const static std::string DEFAULT_CACHE_FOLDERNAME;
    QUrl _url;
    QDateTime _date;
    QString _name;
    QString _user;
    QUrl _cacheUrl;
    QUrl _thumbnail;
    UndoStack* _undoStack = nullptr;
    QQmlObjectListModel<Graph> _graphs;
    Graph* _graph = nullptr;
    bool _autoRefresh = true;
};

} // namespace
