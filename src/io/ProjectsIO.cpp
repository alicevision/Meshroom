#include "ProjectsIO.hpp"
#include "JobsIO.hpp"
#include "models/ProjectModel.hpp"
#include "models/JobModel.hpp"
#include <QDir>

namespace mockup
{

ProjectModel* ProjectsIO::create(QObject* parent)
{
    return new ProjectModel(parent);
}

ProjectModel* ProjectsIO::load(QObject* parent, const QUrl& url)
{
    if(!url.isValid())
    {
        qCritical("Loading project : invalid project URL (malformed or empty URL)");
        return nullptr;
    }

    QDir dir(url.toLocalFile());
    if(!dir.exists())
    {
        qCritical("Loading project : invalid project URL (not found)");
        return nullptr;
    }

    if(!dir.cd("reconstructions"))
    {
        qCritical("Loading project : invalid project URL (invalid structure)");
        return nullptr;
    }

    // create a new ProjectModel and set its URL attribute
    ProjectModel* projectModel = ProjectsIO::create(parent);
    projectModel->setUrl(url);

    return projectModel;
}

bool ProjectsIO::save(ProjectModel& projectModel)
{
    if(!projectModel.url().isValid())
    {
        qCritical("Saving project: invalid project URL (malformed or empty URL)");
        return false;
    }
    QDir dir(projectModel.url().toLocalFile());
    if(!dir.mkpath("reconstructions"))
    {
        qCritical("Saving project: unable to create directory structure");
        return false;
    }
    return true;
}

} // namespace
