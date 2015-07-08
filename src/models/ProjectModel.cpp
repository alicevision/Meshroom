#include "ProjectModel.hpp"
#include "JobModel.hpp"
#include <QDateTime>
#include <QDir>

namespace mockup
{

ProjectModel::ProjectModel(const QUrl& url, QObject* parent)
    : QObject(parent)
    , _url(url)
    , _io(*this)
{
    loadFromDisk();
}

ProjectModel::~ProjectModel()
{
    if(_tmpJob)
        delete _tmpJob;
}

const QString& ProjectModel::name() const
{
    return _name;
}

void ProjectModel::setName(const QString& name)
{
    if(name == _name)
        return;
    _name = name;
    emit nameChanged();
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
    loadFromDisk();
    emit urlChanged();
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

QObject* ProjectModel::tmpJob() const
{
    return _tmpJob;
}

void ProjectModel::setTmpJob(QObject* job)
{
    JobModel* jobmodel = qobject_cast<JobModel*>(job);
    if(!jobmodel)
        return;
    if(jobmodel == _tmpJob)
        return;
    _tmpJob = jobmodel;
    emit tmpJobChanged();
}

void ProjectModel::newTmpJob()
{
    if(_tmpJob)
        delete _tmpJob;
    QDateTime jobtime = QDateTime::currentDateTime();
    QString jobdate = jobtime.toString("yyyy-MM-dd HH:mm");
    QString dirname = jobtime.toString("yyyyMMdd_HHmm");
    QDir dir(_url.toLocalFile()); // project dir
    dir.cd("reconstructions");
    _tmpJob = new JobModel(dir.absoluteFilePath(dirname), this);
    _tmpJob->setUrl(QUrl::fromLocalFile(dir.absoluteFilePath(dirname)));
    _tmpJob->setDate(jobdate);
    emit tmpJobChanged();
}

bool ProjectModel::addTmpJob()
{
    if(!_tmpJob)
        return false;
    if(!_tmpJob->saveToDisk())
        return false;
    _tmpJob->start();
    _jobs.append(_tmpJob);
    _tmpJob = nullptr;
    emit tmpJobChanged();
    emit jobsChanged();
    return true;
}

ProjectModel::ERROR_TYPE ProjectModel::error() const
{
    return _error;
}

QString ProjectModel::errorString() const
{
    switch(_error)
    {
        case ERR_INVALID_URL:
            return "Invalid URL";
        case ERR_INVALID_DESCRIPTOR:
            return "Invalid descriptor file";
        case ERR_MALFORMED_DESCRIPTOR:
            return "Malformed descriptor file";
        case ERR_NOERROR:
            return "";
    }
    return "";
}

void ProjectModel::setError(ERROR_TYPE e)
{
    if(_error == e)
        return;
    _error = e;
}

bool ProjectModel::loadFromDisk()
{
    return _io.load();
}

bool ProjectModel::saveToDisk() const
{
    return _io.save();
}

} // namespace
