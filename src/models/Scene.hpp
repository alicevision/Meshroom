#pragma once

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

public:
    enum BuildMode
    {
        LOCAL = 0,
        DISTRIBUTED = 1
    };
    Q_ENUMS(BuildMode)

public:
    Scene(const QUrl& = QUrl());

public slots:
    const QUrl& url() const { return _url; }
    const QString& name() const { return _name; }
    const QDateTime& date() const { return _date; }
    const QString& user() const { return _user; }
    const QUrl& thumbnail() const { return _thumbnail; }
    const bool& dirty() const { return _dirty; }
    void setUrl(const QUrl&);
    void setName(const QString&);
    void setDate(const QDateTime&);
    void setUser(const QString&);
    void setThumbnail(const QUrl&);
    void setDirty(const bool&);
    bool load();
    bool save();
    void erase();
    void reset();
    bool build(const BuildMode&);

private:
    void serializeToJSON(QJsonObject*) const;
    void deserializeFromJSON(const QJsonObject&);

signals:
    void urlChanged();
    void nameChanged();
    void dateChanged();
    void userChanged();
    void thumbnailChanged();
    void dirtyChanged();

private:
    QUrl _url;
    QDateTime _date;
    QString _name;
    QString _user;
    QUrl _thumbnail;
    bool _dirty;
};

} // namespace
