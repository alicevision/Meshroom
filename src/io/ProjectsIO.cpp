#include "ProjectsIO.hpp"
#include "models/ProjectModel.hpp"
#include "models/JobModel.hpp"
#include <QDir>

namespace mockup
{

ProjectsIO::ProjectsIO(ProjectModel& projectModel)
    : QObject(&projectModel)
    , _project(projectModel)
{
}

bool ProjectsIO::load()
{
    // set as clean
    _project.setError(ProjectModel::ERR_NOERROR);

    if(!_project.url().isValid())
    {
        _project.setError(ProjectModel::ERR_INVALID_URL);
        return false;
    }

    QDir dir(_project.url().toLocalFile());
    if(!dir.exists())
    {
        _project.setError(ProjectModel::ERR_INVALID_URL);
        return false;
    }

    // set project name
    _project.setName(dir.dirName());

    // retrieve project jobs
    if(!dir.cd("reconstructions"))
    {
        _project.setError(ProjectModel::ERR_INVALID_URL);
        return false;
    }

    QStringList jobs = dir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
    QList<QObject*> validJobs;
    for(size_t i = 0; i < jobs.length(); ++i)
    {
        JobModel* job = new JobModel(QUrl::fromLocalFile(dir.absoluteFilePath(jobs[i])), &_project);
        if(job->error() != JobModel::ERR_NOERROR)
        {
            delete job;
            continue;
        }
        validJobs.append(job);
    }
    _project.setJobs(validJobs);

    return true;
}

bool ProjectsIO::save() const
{
    // set as clean
    _project.setError(ProjectModel::ERR_NOERROR);

    if(!_project.url().isValid())
    {
        _project.setError(ProjectModel::ERR_INVALID_URL);
        return false;
    }

    // create reconstruction dir
    QDir dir(_project.url().toLocalFile());
    if(!dir.mkpath("reconstructions"))
    {
        _project.setError(ProjectModel::ERR_INVALID_URL);
        return false;
    }
    return true;
}

} // namespace
