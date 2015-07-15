#include "ProjectModel.hpp"
#include "JobModel.hpp"
#include "ApplicationModel.hpp"
#include "io/ProjectsIO.hpp"
#include "io/SettingsIO.hpp"
#include "io/JobsIO.hpp"
#include <QDateTime>
#include <QDir>

namespace mockup
{

ProjectModel::ProjectModel(QObject* parent)
    : QObject(parent)
{
}

const QString& ProjectModel::name() const
{
    return _name;
}

const QUrl& ProjectModel::url() const
{
    return _url;
}

void ProjectModel::setUrl(const QUrl& url)
{
    if((_url == url) || url.isEmpty())
        return;
    _url = url;
    _name = url.fileName();

    JobsIO::loadAllJobs(*this);

    emit urlChanged();
    emit nameChanged();
}

const QList<QObject*>& ProjectModel::jobs() const
{
    return _jobs;
}

void ProjectModel::setJobs(const QList<QObject*>& jobs)
{
    if(jobs == _jobs)
        return;
    _jobs = jobs;
    emit jobsChanged();
}

QObject* ProjectModel::addJob()
{
    JobModel* jobModel = JobsIO::create(this);
    QDateTime jobtime = QDateTime::currentDateTime();
    QString jobdate = jobtime.toString("yyyy-MM-dd HH:mm");
    QString dirname = jobtime.toString("yyyyMMdd_HHmm");
    QDir dir(_url.toLocalFile());
    dir.cd("reconstructions");
    jobModel->setUrl(QUrl::fromLocalFile(dir.absoluteFilePath(dirname)));
    jobModel->setDate(jobdate);
    _jobs.append(jobModel);
    emit jobsChanged();
    return jobModel;
}

void ProjectModel::removeJob(QObject* model)
{
    JobModel* jobModel = qobject_cast<JobModel*>(model);
    if(!jobModel)
        return;
    delete jobModel;
    if(_jobs.removeAll(jobModel) > 0)
        emit jobsChanged();
}

bool ProjectModel::save()
{
    if(!ProjectsIO::save(*this))
        return false;
    ApplicationModel* applicationModel = qobject_cast<ApplicationModel*>(parent());
    if(applicationModel)
        SettingsIO::saveRecentProjects(*applicationModel);
    return true;
}

} // namespace
