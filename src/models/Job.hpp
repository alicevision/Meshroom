#pragma once

#include <QObject>
#include <QUrl>
#include <QDateTime>
#include <QProcess>
#include "StepModel.hpp"
#include "ResourceModel.hpp"

namespace meshroom
{

class Project;  // forward declaration
class JobModel; // forward declaration

class Job : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QUrl url READ url CONSTANT)
    Q_PROPERTY(QDateTime date READ date CONSTANT)
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QString user READ user CONSTANT)
    Q_PROPERTY(float completion READ completion NOTIFY completionChanged)
    Q_PROPERTY(StatusType status READ status NOTIFY statusChanged)
    Q_PROPERTY(QUrl thumbnail READ thumbnail WRITE setThumbnail NOTIFY thumbnailChanged)
    Q_PROPERTY(StepModel* steps READ steps CONSTANT)
    Q_PROPERTY(ResourceModel* images READ images CONSTANT)

public:
    enum StatusType
    {
        BLOCKED = 0,
        READY = 1,
        RUNNING = 2,
        DONE = 3,
        ERROR = 4,
        CANCELED = 5,
        PAUSED = 6,
        NOTSTARTED = -1,
        SYSTEMERROR = -2
    };
    Q_ENUMS(StatusType)

public:
    Job(Project* project = nullptr);

public:
    Project* project() const { return _project; }

public:
    const QUrl& url() const { return _url; }
    const QString& name() const { return _name; }
    const QDateTime& date() const { return _date; }
    const QString& user() const { return _user; }
    const float& completion() const { return _completion; }
    const StatusType& status() const { return _status; }
    const QUrl& thumbnail() const { return _thumbnail; }
    StepModel* steps() const { return _steps; }
    ResourceModel* images() const { return _images; }
    void setUrl(const QUrl& url);
    void setName(const QString& name);
    void setCompletion(const float& completion);
    void setStatus(const StatusType& status);
    void setThumbnail(const QUrl& thumbnail);
    void setModelIndex(const QModelIndex& id);

public:
    bool load(const QUrl& url);
    bool load(const Job& job);
    void autoSaveOn();
    void autoSaveOff();

public slots:
    bool save();
    bool start(bool local = false);
    void refresh();
    void erase();
    void readProcessOutput(int exitCode, QProcess::ExitStatus s);
    void selectThumbnail();
    bool isStoredOnDisk();
    bool isStartable();
    bool isPairA(const QUrl& url);
    bool isPairB(const QUrl& url);
    bool isPairValid();

private:
    void createDefaultGraph();
    void serializeToJSON(QJsonObject* obj) const;
    void deserializeFromJSON(const QJsonObject& obj);

signals:
    void nameChanged();
    void completionChanged();
    void statusChanged();
    void thumbnailChanged();
    void dataChanged(const QModelIndex&, const QModelIndex&);

private:
    Project* _project = nullptr;
    QUrl _url;
    QDateTime _date;
    QString _name;
    QString _user;
    float _completion = 0.f;
    StatusType _status = NOTSTARTED;
    QUrl _thumbnail;
    StepModel* _steps;
    ResourceModel* _images;
    QPersistentModelIndex _modelIndex;
};

} // namespace
