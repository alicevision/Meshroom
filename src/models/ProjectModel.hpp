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

public:
    ProjectModel(QObject* parent);
    ~ProjectModel() = default;

public slots:
    const QString& name() const;
    const QUrl& url() const;
    void setUrl(const QUrl& url);
    const QList<QObject*>& jobs() const;
    void setJobs(const QList<QObject*>& name);
    QObject* addJob();
    void removeJob(QObject* model);

public slots:
    bool save();

signals:
    void nameChanged();
    void urlChanged();
    void jobsChanged();
    void tmpJobChanged();

private:
    QString _name;
    QUrl _url;
    QList<QObject*> _jobs;
};

} // namespace
