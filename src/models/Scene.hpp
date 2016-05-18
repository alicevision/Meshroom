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
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QDateTime date READ date WRITE setDate NOTIFY dateChanged)
    Q_PROPERTY(QString user READ user WRITE setUser NOTIFY userChanged)
    Q_PROPERTY(QUrl thumbnail READ thumbnail WRITE setThumbnail NOTIFY thumbnailChanged)
    Q_PROPERTY(bool dirty READ dirty WRITE setDirty NOTIFY dirtyChanged)
    Q_PROPERTY(Graph* graph READ graph CONSTANT)

public:
    enum BuildMode
    {
        LOCAL = 0,
        DISTRIBUTED = 1
    };
    Q_ENUMS(BuildMode)

public:
    Scene() = default;
    Scene(QObject* parent, const QUrl& = QUrl());

public:
    Q_SLOT const QUrl& url() const { return _url; }
    Q_SLOT const QString& name() const { return _name; }
    Q_SLOT const QDateTime& date() const { return _date; }
    Q_SLOT const QString& user() const { return _user; }
    Q_SLOT const QUrl& thumbnail() const { return _thumbnail; }
    Q_SLOT const bool& dirty() const { return _dirty; }
    Q_SLOT Graph* graph() const { return _graph; }
    Q_SLOT void setUrl(const QUrl&);
    Q_SLOT void setName(const QString&);
    Q_SLOT void setDate(const QDateTime&);
    Q_SLOT void setUser(const QString&);
    Q_SLOT void setThumbnail(const QUrl&);
    Q_SLOT void setDirty(const bool&);
    Q_SLOT bool load();
    Q_SLOT bool save();
    Q_SLOT void erase();
    Q_SLOT void reset();
    Q_SLOT bool build(const BuildMode&);
    Q_SIGNAL void urlChanged();
    Q_SIGNAL void nameChanged();
    Q_SIGNAL void dateChanged();
    Q_SIGNAL void userChanged();
    Q_SIGNAL void thumbnailChanged();
    Q_SIGNAL void dirtyChanged();

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
    Graph* _graph = new Graph(this);
};

} // namespace
