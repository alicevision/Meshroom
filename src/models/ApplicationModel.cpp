#include "ApplicationModel.hpp"
#include "ProjectModel.hpp"
#include "LogModel.hpp"
#include "Application.hpp"
#include "io/ProjectsIO.hpp"
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

const QList<QObject*>& ApplicationModel::logs() const
{
    return _logs;
}

void ApplicationModel::addLog(QObject* log)
{
    _logs.append(log);
    emit logsChanged();
}

void ApplicationModel::setLogs(const QList<QObject*>& logs)
{
    if(logs == _logs)
        return;
    _logs = logs;
    emit logsChanged();
}

QObject* ApplicationModel::addNewProject()
{
    ProjectModel* projectModel = ProjectsIO::create(this);
    _projects.append(projectModel);
    emit projectsChanged();
    return projectModel;
}

QObject* ApplicationModel::addExistingProject(const QUrl& url)
{
    ProjectModel* projectModel = ProjectsIO::load(this, url);
    if(!projectModel)
        return nullptr;
    _projects.append(projectModel);
    emit projectsChanged();
    SettingsIO::saveRecentProjects(*this);
    return projectModel;
}

void ApplicationModel::removeProject(QObject* model)
{
    ProjectModel* projectModel = qobject_cast<ProjectModel*>(model);
    if(!projectModel)
        return;
    delete projectModel;
    if(_projects.removeAll(projectModel) > 0)
        emit projectsChanged();
    SettingsIO::saveRecentProjects(*this);
}

// private
void ApplicationModel::exposeToQML()
{
    if(_application.engine().rootContext())
        _application.engine().rootContext()->setContextProperty("_applicationModel", this);
}

} // namespace
