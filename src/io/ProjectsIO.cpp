#include "ProjectsIO.hpp"
#include "models/Project.hpp"
#include "models/Resource.hpp"
#include <QDir>

namespace meshroom
{

void ProjectsIO::populate(Project& project)
{
    // list sub-directories to retrieve all jobs
    QDir dir(project.url().toLocalFile());
    dir.cd("reconstructions");
    QStringList jobs = dir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);
    for(size_t i = 0; i < jobs.length(); ++i)
    {
        Job* job = new Job(QUrl::fromLocalFile(dir.absoluteFilePath(jobs[i])));
        project.jobs()->addJob(job);
    }
    // we should have at least one job
    if(project.jobs()->rowCount() <= 0)
        project.jobs()->addJob(project.url());
}

} // namespace
