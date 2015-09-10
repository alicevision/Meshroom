#pragma once

#include <QObject>
#include <QUrl>

namespace mockup
{

class JobModel; // forward declaration

class ProjectModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString name READ name NOTIFY nameChanged)
    Q_PROPERTY(QUrl url READ url WRITE setUrl NOTIFY urlChanged)
    Q_PROPERTY(QList<QObject*> jobs READ jobs WRITE setJobs NOTIFY jobsChanged)
    Q_PROPERTY(QObject* currentJob READ currentJob WRITE setCurrentJob NOTIFY currentJobChanged)

public:
    ProjectModel(QObject* parent = nullptr);
    ~ProjectModel() = default;

public slots:
    const QString& name() const;
    const QUrl& url() const;
    void setUrl(const QUrl& url);
    const QList<QObject*>& jobs() const;
    void setJobs(const QList<QObject*>& name);
    QObject* addJob();
    void removeJob(QObject* model);
    QObject* currentJob();
    void setCurrentJob(QObject* jobModel);

public slots:
    void select();
    void remove();

signals:
    void nameChanged();
    void urlChanged();
    void jobsChanged();
    void currentJobChanged();

private:
    QString _name;
    QUrl _url;
    QList<QObject*> _jobs;
    QObject* _currentJob = nullptr;
};

} // namespace
