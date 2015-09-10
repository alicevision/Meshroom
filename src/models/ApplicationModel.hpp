#pragma once

#include <QObject>
#include <QQmlApplicationEngine>

namespace mockup
{

class ProjectModel; // forward declaration

class ApplicationModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QList<QObject*> projects READ projects WRITE setProjects NOTIFY projectsChanged)
    Q_PROPERTY(QStringList locations READ locations WRITE setLocations NOTIFY locationsChanged)
    Q_PROPERTY(QList<QObject*> logs READ logs WRITE setLogs NOTIFY logsChanged)
    Q_PROPERTY(QObject* currentProject READ currentProject WRITE setCurrentProject NOTIFY
                   currentProjectChanged)

public:
    ApplicationModel(QQmlApplicationEngine& engine);
    ~ApplicationModel();

public slots:
    const QList<QObject*>& projects() const { return _projects; }
    const QStringList& locations() const { return _locations; }
    const QList<QObject*>& logs() const { return _logs; }
    QObject* currentProject() { return _currentProject; }
    void setProjects(const QList<QObject*>& projects);
    void setLocations(const QStringList& locations);
    void setLogs(const QList<QObject*>& logs);
    void setCurrentProject(QObject* projectModel);
    void addProject(const QUrl& url);
    void addLog(QObject* log);
    void removeProject(QObject* projectModel);

public slots:
    void onEngineLoaded(QObject* object, const QUrl& url);

signals:
    void projectsChanged();
    void locationsChanged();
    void logsChanged();
    void currentProjectChanged();

private:
    void exposeToQML();

private:
    QList<QObject*> _projects;
    QObject* _currentProject = nullptr;
    QList<QObject*> _logs;
    QStringList _locations;
};

} // namespaces
