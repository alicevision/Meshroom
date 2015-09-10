#include "ProjectsIO.hpp"
#include "models/ProjectModel.hpp"

namespace mockup
{

ProjectModel* ProjectsIO::create(QObject* parent)
{
    return new ProjectModel(parent);
}

ProjectModel* ProjectsIO::load(QObject* parent, const QUrl& url)
{
    ProjectModel* projectModel = ProjectsIO::create(parent);
    projectModel->setUrl(url);
    return projectModel;
}

} // namespace
