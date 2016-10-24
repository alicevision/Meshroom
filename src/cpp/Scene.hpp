#pragma once

#include "Graph.hpp"
#include <QObject>
#include <QUrl>
#include <QDateTime>
#include <QProcess>

namespace meshroom
{

class SceneModel; // forward declaration

class Scene : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url NOTIFY urlChanged)
    Q_PROPERTY(QString name READ name NOTIFY nameChanged)
    Q_PROPERTY(QDateTime date READ date NOTIFY dateChanged)
    Q_PROPERTY(QString user READ user NOTIFY userChanged)
    Q_PROPERTY(QUrl thumbnail READ thumbnail WRITE setThumbnail NOTIFY thumbnailChanged)
    Q_PROPERTY(bool dirty READ dirty WRITE setDirty NOTIFY dirtyChanged)
    Q_PROPERTY(Graph* graph READ graph CONSTANT)

public:
    Scene();
    Scene(QObject* parent, const QUrl& = QUrl());

public:
    Q_SLOT const QUrl& url() const { return _url; }
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT const QDateTime& date() const { return _date; }
    Q_SLOT const QString& user() const { return _user; }
    Q_SLOT const QUrl& thumbnail() const { return _thumbnail; }
    Q_SLOT const bool& dirty() const { return _dirty; }
    Q_SLOT Graph* graph() const { return _graph; }
    Q_SLOT void setThumbnail(const QUrl&);
    Q_SLOT void setDirty(const bool&);
    Q_SLOT bool load(const QUrl&);
    Q_SLOT bool import(const QUrl&);
    Q_SLOT bool save();
    Q_SLOT bool saveAs(const QUrl&);
    Q_SLOT void erase();
    Q_SLOT void reset();
    Q_SIGNAL void urlChanged();
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void dateChanged();
    Q_SIGNAL void userChanged();
    Q_SIGNAL void thumbnailChanged();
    Q_SIGNAL void dirtyChanged();

private:
    void setUrl(const QUrl&);
    void setName(const QString&);
    void setDate(const QDateTime&);
    void setUser(const QString&);

private:
    QJsonObject serializeToJSON() const;
    void deserializeFromJSON(const QJsonObject&);

private:
    QUrl _url;
    QDateTime _date;
    QString _name;
    QString _user;
    QUrl _thumbnail;
    bool _dirty = false;
    Graph* _graph = nullptr;
};

} // namespace
