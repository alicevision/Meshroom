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
    if(_jobs.isEmpty())
        addJob();
    setCurrentJob(_jobs[0]);

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
    QDateTime jobtime = QDateTime::currentDateTime();
    QString dirname = jobtime.toString("yyyyMMdd_HHmmss");
    QUrl url = QUrl::fromLocalFile(_url.toLocalFile() + "/reconstructions/" + dirname);
    JobModel* jobModel = JobsIO::load(this, url);
    if(!jobModel)
        return nullptr;
    _jobs.append(jobModel);
    emit jobsChanged();
    return jobModel;
}

void ProjectModel::removeJob(QObject* model)
{
    JobModel* jobModel = qobject_cast<JobModel*>(model);
    if(!jobModel)
        return;
    int id = _jobs.indexOf(jobModel);
    if(id < 0)
        return;
    _jobs.removeAt(id);
    if(_jobs.isEmpty())
        addJob();
    setCurrentJob((id < _jobs.count()) ? _jobs.at(id) : _jobs.last());
    emit jobsChanged();
    delete jobModel;
}

QObject* ProjectModel::currentJob()
{
    return _currentJob;
}

void ProjectModel::setCurrentJob(QObject* jobModel)
{
    select(); // ensure that this project is selected
    if(jobModel == _currentJob)
        return;
    _currentJob = jobModel;
    emit currentJobChanged();
}

void ProjectModel::select()
{
    ApplicationModel* app = qobject_cast<ApplicationModel*>(parent());
    if(!app)
        return;
    app->setCurrentProject(this);
}

void ProjectModel::remove()
{
    ApplicationModel* app = qobject_cast<ApplicationModel*>(parent());
    if(!app)
        return;
    app->removeProject(this);
}

} // namespace
