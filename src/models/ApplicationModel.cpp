#include "ApplicationModel.hpp"
#include "ProjectModel.hpp"
#include "Application.hpp"
#include <QtQml/QQmlContext>

namespace mockup
{

ApplicationModel::ApplicationModel(Application& app)
    : QObject(&app)
    , _application(app)
{
    exposeToQML();
}

const QList<QObject*>& ApplicationModel::projects() const
{
    return _projects;
}

void ApplicationModel::setProjects(const QList<QObject*>& projects)
{
    if(projects == _projects)
        return;
    _projects = projects;
    emit projectsChanged();
}

void ApplicationModel::clear()
{
    _projects.clear();
    _application.settings().clearRecentProjects();
    emit projectsChanged();
}

void ApplicationModel::removeProject(QObject* projectModel)
{
    ProjectModel* project = qobject_cast<ProjectModel*>(projectModel);
    if(!project)
        return;
    QUrl url = project->url();
    if(_projects.removeAll(projectModel) > 0)
    {
        _application.settings().removeFromRecentProjects(url);
        emit projectsChanged();
    }
}

QObject* ApplicationModel::tmpProject()
{
    if(!_tmpProject)
        _tmpProject = new ProjectModel(QUrl(), this);
    return _tmpProject;
}

bool ApplicationModel::addTmpProject()
{
    if(!_tmpProject->saveToDisk())
        return false;
    _projects.append(_tmpProject);
    _application.settings().addToRecentProjects(_tmpProject->url());
    _tmpProject = nullptr;
    emit projectsChanged();
    return true;
}

// private
void ApplicationModel::exposeToQML()
{
    if(_application.engine().rootContext())
        _application.engine().rootContext()->setContextProperty("_applicationModel", this);
}

} // namespace
