#pragma once

#include <QObject>

namespace mockup
{

class Application; // forward declaration
class ProjectModel; // forward declaration

class ApplicationModel : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QList<QObject*> projects READ projects WRITE setProjects NOTIFY projectsChanged)

public:
    ApplicationModel(Application& app);
    ~ApplicationModel() = default;

public:
    const QList<QObject*>& projects() const;
    void setProjects(const QList<QObject*>& projects);

public slots:
    void clear();
    QObject* tmpProject();
    bool addTmpProject();

signals:
    void projectsChanged();

private:
    void exposeToQML();

private:
    QList<QObject*> _projects;
    Application& _application;
    ProjectModel* _tmpProject = nullptr;
};

} // namespaces
