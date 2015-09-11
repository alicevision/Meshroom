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
    Q_PROPERTY(QList<QObject*> logs READ logs WRITE setLogs NOTIFY logsChanged)
    Q_PROPERTY(QStringList featuredProjects READ featuredProjects WRITE setFeaturedProjects NOTIFY featuredProjectsChanged)
    Q_PROPERTY(QObject* currentProject READ currentProject WRITE setCurrentProject NOTIFY
                   currentProjectChanged)

public:
    ApplicationModel(QQmlApplicationEngine& engine);
    ~ApplicationModel();

public slots:
    const QList<QObject*>& projects() const { return _projects; }
    const QList<QObject*>& logs() const { return _logs; }
    const QStringList& featuredProjects() const { return _featuredProjects; }
    QObject* currentProject() { return _currentProject; }
    void setProjects(const QList<QObject*>& projects);
    void setLogs(const QList<QObject*>& logs);
    void setFeaturedProjects(const QStringList& locations);
    void setCurrentProject(QObject* projectModel);
    void addProject(const QUrl& url);
    void addLog(QObject* log);
    void removeProject(QObject* projectModel);

public slots:
    void onEngineLoaded(QObject* object, const QUrl& url);

signals:
    void projectsChanged();
    void logsChanged();
    void featuredProjectsChanged();
    void currentProjectChanged();

private:
    void exposeToQML();

private:
    QList<QObject*> _projects;
    QList<QObject*> _logs;
    QObject* _currentProject = nullptr;
    QStringList _featuredProjects;
};

} // namespaces
