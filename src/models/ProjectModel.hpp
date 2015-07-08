#pragma once

#include "io/ProjectsIO.hpp"
#include <QObject>
#include <QUrl>

namespace mockup
{

class JobModel; // forward declaration

class ProjectModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name WRITE setName NOTIFY nameChanged)
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QList<QObject*> jobs READ jobs WRITE setJobs NOTIFY jobsChanged)
    Q_PROPERTY(QObject* tmpJob READ tmpJob WRITE setTmpJob NOTIFY tmpJobChanged)

public:
    enum ERROR_TYPE
    {
        ERR_NOERROR = 0,
        ERR_INVALID_URL,
        ERR_INVALID_DESCRIPTOR,
        ERR_MALFORMED_DESCRIPTOR
    };

public:
    ProjectModel(const QUrl& url, QObject* parent);
    ~ProjectModel();

public slots:
    const QString& name() const;
    void setName(const QString& name);
    const QUrl& url() const;
    void setUrl(const QUrl& url);
    const QList<QObject*>& jobs() const;
    void setJobs(const QList<QObject*>& name);

    QObject* tmpJob() const;
    void setTmpJob(QObject* job);
    void newTmpJob();
    bool addTmpJob();

public slots:
    ERROR_TYPE error() const;
    QString errorString() const;
    void setError(ERROR_TYPE e);

public slots:
    bool loadFromDisk();
    bool saveToDisk() const;

signals:
    void nameChanged();
    void urlChanged();
    void jobsChanged();
    void tmpJobChanged();

private:
    QString _name;
    QUrl _url;
    QList<QObject*> _jobs;
    JobModel* _tmpJob = nullptr;
    ERROR_TYPE _error = ERR_NOERROR;
    ProjectsIO _io;
};

} // namespace
