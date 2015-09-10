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
    Q_PROPERTY(QObject* currentProject READ currentProject WRITE setCurrentProject NOTIFY
                   currentProjectChanged)
    Q_PROPERTY(QStringList locations READ locations WRITE setLocations NOTIFY locationsChanged)
    Q_PROPERTY(QList<QObject*> logs READ logs WRITE setLogs NOTIFY logsChanged)

public:
    ApplicationModel(QQmlApplicationEngine& engine);
    ~ApplicationModel();

public slots:
    const QList<QObject*>& projects() const;
    void setProjects(const QList<QObject*>& projects);
    QObject* addProject(const QUrl& url);
    void removeProject(QObject* projectModel);
    QObject* currentProject();
    void setCurrentProject(QObject* projectModel);
    const QStringList& locations() const;
    void setLocations(const QStringList& locations);
    const QList<QObject*>& logs() const;
    void addLog(QObject* log);
    void setLogs(const QList<QObject*>& logs);

public slots:
    void onEngineLoaded(QObject* object, const QUrl& url);

signals:
    void projectsChanged();
    void currentProjectChanged();
    void locationsChanged();
    void logsChanged();

private:
    void exposeToQML();

private:
    QList<QObject*> _projects;
    QObject* _currentProject = nullptr;
    QList<QObject*> _logs;
    QStringList _locations;
};

} // namespaces
