#include "ProjectsIO.hpp"
#include "models/ProjectModel.hpp"

namespace mockup
{

ProjectModel* ProjectsIO::load(QObject* parent, const QUrl& url)
{
    ProjectModel* projectModel = new ProjectModel(parent);
    projectModel->setUrl(url);
    return projectModel;
}

} // namespace
