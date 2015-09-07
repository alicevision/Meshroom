#include "ApplicationModel.hpp"
#include "ProjectModel.hpp"
#include "LogModel.hpp"
#include "io/ProjectsIO.hpp"
#include "io/SettingsIO.hpp"
#include <QtQml/QQmlContext>
#include <iostream>

namespace mockup
{

namespace
{ // empty namespace

static mockup::ApplicationModel* _logger = nullptr;
void doLog(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    if(!_logger)
        return;
    QByteArray localMsg = msg.toLocal8Bit();
    if(QString(context.file).contains(".qml"))
    {
        std::cerr << localMsg.constData() << std::endl;
        return;
    }
    LogModel* model = new LogModel(type, localMsg.constData(), nullptr);
    _logger->addLog(model);
}

} // empty namespace

ApplicationModel::ApplicationModel(QQmlApplicationEngine& engine)
    : QObject(nullptr)
{
    connect(&engine, SIGNAL(objectCreated(QObject*, const QUrl&)), this,
            SLOT(onEngineLoaded(QObject*, const QUrl&)));

    // load user settings
    SettingsIO::loadRecentProjects(*this);

    // load default project locations
    QStringList locations = {"new location..."};
    QString externalLocationsStr = std::getenv("MOCKUP_PROJECT_LOCATIONS");
    QStringList externalLocations = externalLocationsStr.split(":");
    foreach(const QString& loc, externalLocations)
    {
        if(QUrl::fromLocalFile(loc).isValid())
            locations.append(loc);
    }
    setLocations(locations);

    // expose this object to QML
    if(engine.rootContext())
        engine.rootContext()->setContextProperty("_applicationModel", this);

    // load QML UI
    engine.load(QUrl("src/qml/main.qml"));
}

ApplicationModel::~ApplicationModel()
{
    _logger = this;
    qInstallMessageHandler(0);
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
    int id = _projects.indexOf(projectModel);
    if(id<0)
        return;
    _projects.removeAt(id);
    setCurrentProject((id < _projects.count()) ? _projects.at(id) :
        (_projects.count()!=0)?_projects.last():nullptr);
    emit projectsChanged();
    delete projectModel;
    SettingsIO::saveRecentProjects(*this);
}

QObject* ApplicationModel::currentProject()
{
    return _currentProject;
}

void ApplicationModel::setCurrentProject(QObject* projectModel)
{
    if(projectModel == _currentProject)
        return;
    _currentProject = projectModel;
    emit currentProjectChanged();
}

const QStringList& ApplicationModel::locations() const
{
    return _locations;
}

void ApplicationModel::setLocations(const QStringList& locations)
{
    if(locations == _locations)
        return;
    _locations = locations;
    emit locationsChanged();
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

void ApplicationModel::onEngineLoaded(QObject* object, const QUrl& url)
{
    // setup a custom logging system
    _logger = this;
    qInstallMessageHandler(doLog);
}

} // namespace
